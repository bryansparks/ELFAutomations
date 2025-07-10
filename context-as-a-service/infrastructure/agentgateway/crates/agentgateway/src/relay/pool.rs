use crate::outbound;
// Import for the protobuf type Target_OpenAPITarget
use crate::proto::agentgateway::dev::mcp::target::target::OpenApiTarget as ProtoXdsOpenApiTarget;

use super::*;
use futures::{FutureExt, StreamExt, future::BoxFuture, stream::BoxStream};
use reqwest::{Client as HttpClient, IntoUrl, Url, header::ACCEPT};
use rmcp::model::ClientJsonRpcMessage;
use rmcp::service::{Peer, serve_client_with_ct};
use rmcp::transport::sse::{SseClient, SseTransportError};
use rmcp::{ClientHandler, ServiceError};
use sse_stream::{Error as SseError, Sse, SseStream};

pub(crate) struct ConnectionPool {
	listener_name: String,
	state: Arc<tokio::sync::RwLock<XdsStore>>,
	by_name: HashMap<String, upstream::UpstreamTarget>,
}

impl ConnectionPool {
	pub(crate) fn new(state: Arc<tokio::sync::RwLock<XdsStore>>, listener_name: String) -> Self {
		Self {
			listener_name,
			state,
			by_name: HashMap::new(),
		}
	}

	pub(crate) async fn get_or_create(
		&mut self,
		rq_ctx: &RqCtx,
		peer: &Peer<RoleServer>,
		name: &str,
	) -> anyhow::Result<&upstream::UpstreamTarget> {
		// Connect if it doesn't exist
		if !self.by_name.contains_key(name) {
			// Read target info and drop lock before calling connect
			let target_info: Option<(
				outbound::Target<outbound::McpTargetSpec>,
				tokio_util::sync::CancellationToken,
			)> = {
				let state = self.state.read().await;
				state
					.mcp_targets
					.get(name, &self.listener_name)
					.map(|(target, ct)| (target.clone(), ct.clone()))
			};

			if let Some((target, ct)) = target_info {
				// Now self is not immutably borrowed by state lock
				self.connect(rq_ctx, &ct, &target, peer).await?;
			} else {
				// Handle target not found in state configuration
				return Err(anyhow::anyhow!(
					"Target configuration not found for {}",
					name
				));
			}
		}
		let target = self.by_name.get(name);
		Ok(target.ok_or(McpError::invalid_request(
			format!("Service {} not found", name),
			None,
		))?)
	}

	pub(crate) async fn remove(&mut self, name: &str) -> Option<upstream::UpstreamTarget> {
		self.by_name.remove(name)
	}

	pub(crate) async fn list(
		&mut self,
		rq_ctx: &RqCtx,
		peer: &Peer<RoleServer>,
	) -> anyhow::Result<Vec<(String, &upstream::UpstreamTarget)>> {
		// Iterate through all state targets, and get the connection from the pool
		// If the connection is not in the pool, connect to it and add it to the pool
		// 1. Get target configurations (name, Target, CancellationToken) from the state's TargetStore
		let targets_config: Vec<(
			String,
			(
				outbound::Target<outbound::McpTargetSpec>,
				tokio_util::sync::CancellationToken,
			),
		)> = {
			let state = self.state.read().await;
			// Iterate the underlying HashMap directly to get the full tuple
			state
				.mcp_targets
				.iter(&self.listener_name)
				.map(|(name, target)| (name.clone(), target.clone()))
				.collect()
		};

		// 2. Identify targets needing connection without holding lock or borrowing self mutably yet
		let mut connections_to_make = Vec::new();
		for (name, (target, ct)) in &targets_config {
			if !self.by_name.contains_key(name) {
				connections_to_make.push((name.clone(), target.clone(), ct.clone()));
			}
		}

		// 3. Connect the missing ones (self is borrowed mutably here)
		for (name, target, ct) in connections_to_make {
			tracing::debug!("Connecting missing target: {}", name);
			self
				.connect(rq_ctx, &ct, &target, peer)
				.await
				.map_err(|e| {
					tracing::error!("Failed to connect target {}: {}", name, e);
					e // Propagate error
				})?;
		}
		tracing::debug!("Finished connecting missing targets.");

		// 4. Collect all required connections from the pool
		let results = targets_config
			.into_iter()
			.filter_map(|(name, _)| {
				self
					.by_name
					.get(&name)
					.map(|target: &upstream::UpstreamTarget| (name, target))
			})
			.collect();

		Ok(results)
	}

	#[instrument(
    level = "debug",
    skip_all,
    fields(
        name=%target.name,
    ),
  )]
	pub(crate) async fn connect(
		&mut self,
		rq_ctx: &RqCtx,
		ct: &tokio_util::sync::CancellationToken,
		target: &outbound::Target<outbound::McpTargetSpec>,
		peer: &Peer<RoleServer>,
	) -> Result<(), anyhow::Error> {
		// Already connected
		if let Some(_transport) = self.by_name.get(&target.name) {
			return Ok(());
		}
		tracing::trace!("connecting to target: {}", target.name);
		let transport: upstream::UpstreamTarget = match &target.spec {
			McpTargetSpec::Sse(sse) => {
				tracing::debug!("starting sse transport for target: {}", target.name);
				let path = match sse.path.as_str() {
					"" => "/sse",
					_ => sse.path.as_str(),
				};
				let builder = reqwest::Client::builder();
				let (scheme, builder) = tls_cfg(builder, &sse.tls, sse.port).await?;

				let url = format!("{}://{}:{}{}", scheme, sse.host, sse.port, path);
				let mut upstream_headers = get_default_headers(&sse.backend_auth, rq_ctx).await?;
				for (key, value) in sse.headers.iter() {
					upstream_headers.insert(
						HeaderName::from_bytes(key.as_bytes())?,
						HeaderValue::from_str(value)?,
					);
				}
				let client = builder.default_headers(upstream_headers).build()?;
				let client = ReqwestSseClient::new_with_client(url.as_str(), client).await?;
				let transport = SseTransport::start_with_client(client).await?;

				upstream::UpstreamTarget {
					filters: target.filters.clone(),
					spec: upstream::UpstreamTargetSpec::Mcp(
						serve_client_with_ct(
							PeerClientHandler {
								peer: peer.clone(),
								peer_client: None,
							},
							transport,
							ct.child_token(),
						)
						.await?,
					),
				}
			},
			McpTargetSpec::Stdio { cmd, args, env: _ } => {
				tracing::debug!("starting stdio transport for target: {}", target.name);
				upstream::UpstreamTarget {
					filters: target.filters.clone(),
					spec: upstream::UpstreamTargetSpec::Mcp(
						serve_client_with_ct(
							PeerClientHandler {
								peer: peer.clone(),
								peer_client: None,
							},
							TokioChildProcess::new(Command::new(cmd).args(args))?,
							ct.child_token(),
						)
						.await?,
					),
				}
			},
			McpTargetSpec::OpenAPI(openapi_target_spec_from_outbound) => {
				// Renamed for clarity
				tracing::debug!("starting OpenAPI transport for target: {}", target.name);

				// 1. Retrieve schema_source
				let current_schema_source_proto = openapi_target_spec_from_outbound
					.schema_source
					.clone()
					.ok_or_else(|| {
					anyhow::anyhow!(
						"OpenAPI target {} is missing schema_source definition",
						target.name
					)
				})?;

				// 2. Prepare for load_openapi_schema
				let proto_target_for_loading = ProtoXdsOpenApiTarget {
					host: openapi_target_spec_from_outbound.host.clone(),
					port: openapi_target_spec_from_outbound.port,
					schema_source: Some(current_schema_source_proto),
					auth: None,      // Not needed for schema loading
					tls: None,       // Not needed for schema loading
					headers: vec![], // Not needed for schema loading
				};

				// 3. Call load_openapi_schema
				let loaded_openapi_doc =
					crate::outbound::openapi::load_openapi_schema(&proto_target_for_loading)
						.await
						.map_err(|e| {
							anyhow::anyhow!(
								"Failed to load OpenAPI schema for target {}: {}",
								target.name,
								e
							)
						})?;

				// 4. Parse Tools and Prefix
				let tools =
					crate::outbound::openapi::parse_openapi_schema(&loaded_openapi_doc).map_err(|e| {
						anyhow::anyhow!(
							"Failed to parse tools from OpenAPI schema for target {}: {}",
							target.name,
							e
						)
					})?;
				let prefix =
					crate::outbound::openapi::get_server_prefix(&loaded_openapi_doc).map_err(|e| {
						anyhow::anyhow!(
							"Failed to get server prefix from OpenAPI schema for target {}: {}",
							target.name,
							e
						)
					})?;

				// 5. Construct openapi::Handler (client setup)
				let builder = reqwest::Client::builder();
				let (scheme, builder) = tls_cfg(
					builder,
					&openapi_target_spec_from_outbound.tls,
					openapi_target_spec_from_outbound.port,
				)
				.await?;

				let mut api_headers =
					get_default_headers(&openapi_target_spec_from_outbound.backend_auth, rq_ctx).await?;
				for (key, value) in &openapi_target_spec_from_outbound.headers {
					api_headers.insert(
						HeaderName::from_bytes(key.as_bytes())?,
						HeaderValue::from_str(value)?,
					);
				}
				let final_client = builder.default_headers(api_headers).build()?;

				upstream::UpstreamTarget {
					filters: target.filters.clone(), // From the outer 'target' variable
					spec: upstream::UpstreamTargetSpec::OpenAPI(crate::outbound::openapi::Handler {
						host: openapi_target_spec_from_outbound.host.clone(),
						client: final_client,
						tools, // From parse_openapi_schema
						scheme: scheme.to_string(),
						prefix, // From get_server_prefix
						port: openapi_target_spec_from_outbound.port,
					}),
				}
			},
		};
		self.by_name.insert(target.name.clone(), transport);
		Ok(())
	}
}

async fn tls_cfg(
	builder: reqwest::ClientBuilder,
	tls: &Option<outbound::TlsConfig>,
	port: u32,
) -> Result<(String, reqwest::ClientBuilder), anyhow::Error> {
	match (port, tls) {
		(443, None) => {
			let builder = builder.https_only(true);
			Ok(("https".to_string(), builder))
		},
		(443, Some(tls)) => {
			let builder = builder
				.https_only(true)
				.danger_accept_invalid_hostnames(tls.insecure_skip_verify);
			Ok(("https".to_string(), builder))
		},
		(_, None) => Ok(("http".to_string(), builder)),
		(_, Some(tls)) => {
			let builder = builder
				.https_only(false)
				.danger_accept_invalid_hostnames(tls.insecure_skip_verify);
			Ok(("https".to_string(), builder))
		},
	}
}

#[derive(Debug, Clone)]
pub(crate) struct PeerClientHandler {
	peer: Peer<RoleServer>,
	peer_client: Option<Peer<RoleClient>>,
}

impl ClientHandler for PeerClientHandler {
	async fn create_message(
		&self,
		params: CreateMessageRequestParam,
		_context: RequestContext<RoleClient>,
	) -> Result<CreateMessageResult, McpError> {
		self.peer.create_message(params).await.map_err(|e| match e {
			ServiceError::McpError(e) => e,
			_ => McpError::internal_error(e.to_string(), None),
		})
	}

	async fn list_roots(
		&self,
		_context: RequestContext<RoleClient>,
	) -> Result<ListRootsResult, McpError> {
		self.peer.list_roots().await.map_err(|e| match e {
			ServiceError::McpError(e) => e,
			_ => McpError::internal_error(e.to_string(), None),
		})
	}

	async fn on_cancelled(&self, params: CancelledNotificationParam) {
		let _ = self.peer.notify_cancelled(params).await.inspect_err(|e| {
			tracing::error!("Failed to notify cancelled: {}", e);
		});
	}

	async fn on_progress(&self, params: ProgressNotificationParam) {
		let _ = self.peer.notify_progress(params).await.inspect_err(|e| {
			tracing::error!("Failed to notify progress: {}", e);
		});
	}

	async fn on_logging_message(&self, params: LoggingMessageNotificationParam) {
		let _ = self
			.peer
			.notify_logging_message(params)
			.await
			.inspect_err(|e| {
				tracing::error!("Failed to notify logging message: {}", e);
			});
	}

	async fn on_prompt_list_changed(&self) {
		let _ = self
			.peer
			.notify_prompt_list_changed()
			.await
			.inspect_err(|e| {
				tracing::error!("Failed to notify prompt list changed: {}", e);
			});
	}

	async fn on_resource_list_changed(&self) {
		let _ = self
			.peer
			.notify_resource_list_changed()
			.await
			.inspect_err(|e| {
				tracing::error!("Failed to notify resource list changed: {}", e);
			});
	}

	async fn on_tool_list_changed(&self) {
		let _ = self.peer.notify_tool_list_changed().await.inspect_err(|e| {
			tracing::error!("Failed to notify tool list changed: {}", e);
		});
	}

	async fn on_resource_updated(&self, params: ResourceUpdatedNotificationParam) {
		let _ = self
			.peer
			.notify_resource_updated(params)
			.await
			.inspect_err(|e| {
				tracing::error!("Failed to notify resource updated: {}", e);
			});
	}

	fn set_peer(&mut self, peer: Peer<RoleClient>) {
		self.peer_client = Some(peer);
	}

	fn get_peer(&self) -> Option<Peer<RoleClient>> {
		self.peer_client.clone()
	}
}

async fn get_default_headers(
	auth_config: &Option<backend::BackendAuthConfig>,
	rq_ctx: &RqCtx,
) -> Result<HeaderMap, anyhow::Error> {
	match auth_config {
		Some(auth_config) => {
			let backend_auth = auth_config.build(&rq_ctx.identity).await?;
			let token = backend_auth.get_token().await?;
			let mut upstream_headers = HeaderMap::new();
			let auth_value = HeaderValue::from_str(&format!("Bearer {}", token))?;
			upstream_headers.insert(AUTHORIZATION, auth_value);
			Ok(upstream_headers)
		},
		None => Ok(HeaderMap::new()),
	}
}

// This is mostly a copy/paste of the upstream ReqwestSseClient, but with the
// ability to dynamically add headers per-request. For example tracing headers,
// or custom headers for the backend.

#[derive(Clone)]
pub struct ReqwestSseClient {
	http_client: HttpClient,
	sse_url: Url,
}

impl ReqwestSseClient {
	pub async fn new_with_client<U>(
		url: U,
		client: HttpClient,
	) -> Result<Self, SseTransportError<reqwest::Error>>
	where
		U: IntoUrl,
	{
		let url = url.into_url()?;
		Ok(Self {
			http_client: client,
			sse_url: url,
		})
	}
}

const MIME_TYPE: &str = "text/event-stream";
const HEADER_LAST_EVENT_ID: &str = "Last-Event-ID";

impl SseClient<reqwest::Error> for ReqwestSseClient {
	fn connect(
		&self,
		last_event_id: Option<String>,
	) -> BoxFuture<
		'static,
		Result<BoxStream<'static, Result<Sse, SseError>>, SseTransportError<reqwest::Error>>,
	> {
		let client = self.http_client.clone();
		let sse_url = self.sse_url.as_ref().to_string();
		let last_event_id = last_event_id.clone();
		let fut = async move {
			let mut request_builder = client.get(&sse_url).header(ACCEPT, MIME_TYPE);
			if let Some(last_event_id) = last_event_id {
				request_builder = request_builder.header(HEADER_LAST_EVENT_ID, last_event_id);
			}
			let response = request_builder.send().await?;
			let response = response.error_for_status()?;
			match response.headers().get(reqwest::header::CONTENT_TYPE) {
				Some(ct) => {
					if !ct.as_bytes().starts_with(MIME_TYPE.as_bytes()) {
						return Err(SseTransportError::UnexpectedContentType(Some(ct.clone())));
					}
				},
				None => {
					return Err(SseTransportError::UnexpectedContentType(None));
				},
			}
			let event_stream = SseStream::from_byte_stream(response.bytes_stream()).boxed();
			Ok(event_stream)
		};
		fut.boxed()
	}

	fn post(
		&self,
		session_id: &str,
		message: ClientJsonRpcMessage,
	) -> BoxFuture<'static, Result<(), SseTransportError<reqwest::Error>>> {
		let client = self.http_client.clone();
		let sse_url = self.sse_url.clone();
		let session_id = session_id.to_string();
		Box::pin(async move {
			let mut headers = HeaderMap::new();
			if let ClientJsonRpcMessage::Request(req) = &message {
				match req.request.extensions().get::<RqCtx>() {
					Some(rq_ctx) => {
						let tracer = trcng::get_tracer();
						let _span = tracer
							.span_builder("sse_post")
							.with_kind(SpanKind::Client)
							.start_with_context(tracer, &rq_ctx.context);
						trcng::add_context_to_request(&mut headers, &rq_ctx.context);
					},
					None => {
						tracing::trace!("No RqCtx found in extensions");
					},
				}
			}
			let uri = sse_url.join(&session_id).map_err(SseTransportError::from)?;
			let request_builder = client.post(uri.as_ref()).json(&message).headers(headers);
			request_builder
				.send()
				.await
				.and_then(|resp| resp.error_for_status())
				.map_err(SseTransportError::from)
				.map(drop)
		})
	}
}
