# Multi-stage build for AgentGateway with TypeScript MCP servers
FROM node:18-alpine AS mcp-builder

# Build TypeScript MCP servers
WORKDIR /app/mcp-servers-ts
COPY mcp-servers-ts/package*.json ./
RUN npm ci --only=production

COPY mcp-servers-ts/ ./
RUN npm run build

# AgentGateway build stage
FROM rust:1.86-alpine AS gateway-builder

# Install system dependencies including protobuf compiler
RUN apk add --no-cache musl-dev npm protobuf-dev

# Build AgentGateway UI
WORKDIR /app/agentgateway
COPY third-party/agentgateway/ ./

WORKDIR /app/agentgateway/ui
RUN npm install && npm run build

# Build AgentGateway binary
WORKDIR /app/agentgateway
ENV MCPGW_BUILD_buildVersion=1.0.0
ENV MCPGW_BUILD_buildGitRevision=main
ENV MCPGW_BUILD_buildStatus=release
ENV MCPGW_BUILD_buildTag=v1.0.0
RUN cargo build --release

# Final runtime stage
FROM node:18-alpine

# Install runtime dependencies
RUN apk add --no-cache curl

# Copy AgentGateway binary
COPY --from=gateway-builder /app/agentgateway/target/release/agentgateway /usr/local/bin/

# Copy built MCP servers
COPY --from=mcp-builder /app/mcp-servers-ts/dist /app/mcp-servers-ts/dist
COPY --from=mcp-builder /app/mcp-servers-ts/node_modules /app/mcp-servers-ts/node_modules
COPY --from=mcp-builder /app/mcp-servers-ts/package.json /app/mcp-servers-ts/

# Copy configuration
COPY config/agentgateway /app/config

# Expose ports
EXPOSE 3000 9091

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Override the Node.js entrypoint script to prevent it from interfering with AgentGateway startup
ENTRYPOINT []
CMD ["agentgateway", "--file", "/app/config/config.json"]
