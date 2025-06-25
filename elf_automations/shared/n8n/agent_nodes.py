"""
N8N AI Agent Node Configurations

Comprehensive configurations for N8N's AI agent nodes including LangChain integrations.
Based on 2024-2025 N8N capabilities.
"""

from typing import Any, Dict, List, Optional


class AgentNodeBuilder:
    """Builder for creating complex AI agent node configurations"""

    @staticmethod
    def create_conversational_agent(
        name: str = "AI Assistant",
        model_provider: str = "openai",
        model: str = "gpt-4",
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        tools: List[Dict[str, Any]] = None,
        memory_enabled: bool = True,
    ) -> Dict[str, Any]:
        """Create a conversational AI agent with optional tools and memory"""

        node = {
            "id": f"agent_{name.lower().replace(' ', '_')}",
            "name": name,
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.5,
            "position": [0, 0],
            "parameters": {},
        }

        # Set agent type based on tools
        if tools:
            node["parameters"]["agent"] = "conversationalAgent"
        else:
            node["parameters"]["agent"] = "conversationalAgent"

        # Configure prompt
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}")
        prompt_parts.append("User: {{ $json.message }}")

        node["parameters"]["prompt"] = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "You are a helpful AI assistant.",
                }
            ]
        }

        # Model configuration
        if model_provider == "openai":
            node["parameters"]["model"] = {
                "modelId": f"@n8n/n8n-nodes-langchain.lmChatOpenAi",
                "temperature": temperature,
                "maxTokens": max_tokens,
                "modelName": model,
            }
        elif model_provider == "anthropic":
            node["parameters"]["model"] = {
                "modelId": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
                "temperature": temperature,
                "maxTokensToSample": max_tokens,
                "modelName": model,
            }
        elif model_provider == "google":
            node["parameters"]["model"] = {
                "modelId": "@n8n/n8n-nodes-langchain.lmChatGooglePalm",
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "modelName": model,
            }

        # Add memory if enabled
        if memory_enabled:
            node["parameters"]["memory"] = {
                "memoryId": "@n8n/n8n-nodes-langchain.memoryBufferMemory",
                "sessionId": "={{ $json.session_id || $executionId }}",
                "returnMessages": True,
                "inputKey": "input",
                "outputKey": "output",
            }

        # Add tools if specified
        if tools:
            node["parameters"]["tools"] = tools

        # Options
        node["parameters"]["options"] = {
            "maxIterations": 10,
            "returnIntermediateSteps": False,
            "handleParsingErrors": True,
        }

        return node

    @staticmethod
    def create_tools_agent(
        name: str = "Tool Agent",
        tools: List[str] = None,
        model_provider: str = "openai",
        model: str = "gpt-4",
    ) -> Dict[str, Any]:
        """Create an agent specifically designed to use tools"""

        available_tools = {
            "calculator": {"toolId": "@n8n/n8n-nodes-langchain.toolCalculator"},
            "browser": {
                "toolId": "@n8n/n8n-nodes-langchain.toolWebBrowser",
                "browserMode": "text",
            },
            "code": {
                "toolId": "@n8n/n8n-nodes-langchain.toolCode",
                "language": "javaScript",
                "description": "Execute JavaScript code",
            },
            "http": {
                "toolId": "@n8n/n8n-nodes-langchain.toolHttpRequest",
                "method": "GET",
                "description": "Make HTTP requests",
            },
            "sql": {
                "toolId": "@n8n/n8n-nodes-langchain.toolSql",
                "database": "postgres",
                "description": "Execute SQL queries",
            },
            "vector_search": {
                "toolId": "@n8n/n8n-nodes-langchain.toolVectorStore",
                "operation": "search",
                "topK": 5,
            },
            "mcp": {
                "toolId": "@n8n/n8n-nodes-langchain.toolMcp",
                "server": "{{ $json.mcp_server }}",
                "tool": "{{ $json.mcp_tool }}",
            },
        }

        # Build tool configuration
        configured_tools = []
        for tool_name in tools or ["calculator", "code"]:
            if tool_name in available_tools:
                configured_tools.append(available_tools[tool_name])

        return {
            "id": f"tools_agent_{name.lower().replace(' ', '_')}",
            "name": name,
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.5,
            "position": [0, 0],
            "parameters": {
                "agent": "toolsAgent",
                "prompt": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI assistant with access to various tools. Use them wisely to help the user.",
                        }
                    ]
                },
                "model": {
                    "modelId": f"@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "modelName": model,
                },
                "tools": configured_tools,
                "options": {"maxIterations": 5, "returnIntermediateSteps": True},
            },
        }

    @staticmethod
    def create_plan_execute_agent(
        name: str = "Planning Agent",
        objective: str = "Complete the user's request",
        tools: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a plan-and-execute agent for complex multi-step tasks"""

        return {
            "id": f"plan_execute_{name.lower().replace(' ', '_')}",
            "name": name,
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.5,
            "position": [0, 0],
            "parameters": {
                "agent": "planAndExecuteAgent",
                "objective": objective,
                "prompt": {
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are a planning agent. Your objective is: {objective}",
                        }
                    ]
                },
                "model": {
                    "modelId": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "modelName": "gpt-4",
                },
                "tools": tools or [],
                "options": {"maxIterations": 10, "handleParsingErrors": True},
            },
        }

    @staticmethod
    def create_react_agent(
        name: str = "ReAct Agent",
        tools: List[Dict[str, Any]] = None,
        examples: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a ReAct (Reasoning and Acting) agent"""

        return {
            "id": f"react_{name.lower().replace(' ', '_')}",
            "name": name,
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.5,
            "position": [0, 0],
            "parameters": {
                "agent": "reActAgent",
                "prompt": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a ReAct agent. Think step-by-step and use tools when needed.",
                        }
                    ]
                },
                "model": {
                    "modelId": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "modelName": "gpt-4",
                },
                "tools": tools or [],
                "examples": examples or [],
                "options": {"maxIterations": 8, "returnIntermediateSteps": True},
            },
        }

    @staticmethod
    def create_openai_functions_agent(
        name: str = "Functions Agent",
        functions: List[Dict[str, Any]] = None,
        model: str = "gpt-4",
    ) -> Dict[str, Any]:
        """Create an OpenAI Functions agent"""

        return {
            "id": f"functions_{name.lower().replace(' ', '_')}",
            "name": name,
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.5,
            "position": [0, 0],
            "parameters": {
                "agent": "openAiFunctionsAgent",
                "model": {
                    "modelId": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "modelName": model,
                },
                "functions": functions or [],
                "options": {"maxIterations": 5},
            },
        }


class VectorStoreNodeBuilder:
    """Builder for vector store nodes used in RAG workflows"""

    @staticmethod
    def create_pinecone_node(
        operation: str = "search",
        index_name: str = "{{ $json.index }}",
        namespace: str = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Create a Pinecone vector store node"""

        node = {
            "id": "vector_store_pinecone",
            "name": "Pinecone Vector Store",
            "type": "@n8n/n8n-nodes-langchain.vectorStorePinecone",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {"operation": operation, "index": index_name, "topK": top_k},
        }

        if namespace:
            node["parameters"]["namespace"] = namespace

        if operation == "insert":
            node["parameters"]["embeddings"] = {
                "embeddingId": "@n8n/n8n-nodes-langchain.embeddingsOpenAi",
                "model": "text-embedding-ada-002",
            }

        return node

    @staticmethod
    def create_supabase_vector_node(
        operation: str = "search", table_name: str = "documents", match_count: int = 5
    ) -> Dict[str, Any]:
        """Create a Supabase vector store node"""

        return {
            "id": "vector_store_supabase",
            "name": "Supabase Vector Store",
            "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "operation": operation,
                "tableName": table_name,
                "matchCount": match_count,
                "embeddings": {
                    "embeddingId": "@n8n/n8n-nodes-langchain.embeddingsOpenAi",
                    "model": "text-embedding-ada-002",
                },
            },
        }

    @staticmethod
    def create_memory_vector_node(
        operation: str = "search", collection_name: str = "default"
    ) -> Dict[str, Any]:
        """Create an in-memory vector store node"""

        return {
            "id": "vector_store_memory",
            "name": "Memory Vector Store",
            "type": "@n8n/n8n-nodes-langchain.vectorStoreMemory",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "operation": operation,
                "collectionName": collection_name,
                "embeddings": {
                    "embeddingId": "@n8n/n8n-nodes-langchain.embeddingsOpenAi",
                    "model": "text-embedding-ada-002",
                },
            },
        }


class MemoryNodeBuilder:
    """Builder for memory nodes used in conversational AI"""

    @staticmethod
    def create_buffer_memory(
        session_id: str = "{{ $json.session_id }}",
        memory_key: str = "chat_history",
        return_messages: bool = True,
    ) -> Dict[str, Any]:
        """Create a buffer memory node"""

        return {
            "id": "memory_buffer",
            "name": "Buffer Memory",
            "type": "@n8n/n8n-nodes-langchain.memoryBufferMemory",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "sessionId": session_id,
                "memoryKey": memory_key,
                "returnMessages": return_messages,
            },
        }

    @staticmethod
    def create_window_memory(
        session_id: str = "{{ $json.session_id }}", window_size: int = 10
    ) -> Dict[str, Any]:
        """Create a window buffer memory node"""

        return {
            "id": "memory_window",
            "name": "Window Memory",
            "type": "@n8n/n8n-nodes-langchain.memoryBufferWindowMemory",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "sessionId": session_id,
                "windowSize": window_size,
                "returnMessages": True,
            },
        }

    @staticmethod
    def create_summary_memory(
        session_id: str = "{{ $json.session_id }}", ai_model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """Create a summary memory node"""

        return {
            "id": "memory_summary",
            "name": "Summary Memory",
            "type": "@n8n/n8n-nodes-langchain.memorySummaryMemory",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "sessionId": session_id,
                "aiModel": ai_model,
                "returnMessages": True,
            },
        }

    @staticmethod
    def create_vector_memory(
        session_id: str = "{{ $json.session_id }}",
        collection_name: str = "conversations",
    ) -> Dict[str, Any]:
        """Create a vector store memory node"""

        return {
            "id": "memory_vector",
            "name": "Vector Memory",
            "type": "@n8n/n8n-nodes-langchain.memoryVectorStore",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "sessionId": session_id,
                "collectionName": collection_name,
                "vectorStore": {
                    "vectorStoreId": "@n8n/n8n-nodes-langchain.vectorStoreMemory"
                },
            },
        }


class ChainNodeBuilder:
    """Builder for creating chain nodes for complex workflows"""

    @staticmethod
    def create_retrieval_qa_chain(
        vector_store_node_name: str,
        model_provider: str = "openai",
        model: str = "gpt-4",
    ) -> Dict[str, Any]:
        """Create a retrieval QA chain for RAG workflows"""

        return {
            "id": "retrieval_qa_chain",
            "name": "Retrieval QA Chain",
            "type": "@n8n/n8n-nodes-langchain.chainRetrievalQa",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "query": "={{ $json.question }}",
                "model": {
                    "modelId": f"@n8n/n8n-nodes-langchain.lmChat{model_provider.title()}",
                    "modelName": model,
                },
                "vectorStore": f"={{{{ ${{{vector_store_node_name}}} }}}}",
                "options": {"returnSourceDocuments": True},
            },
        }

    @staticmethod
    def create_summarization_chain(
        model_provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        chain_type: str = "map_reduce",
    ) -> Dict[str, Any]:
        """Create a summarization chain"""

        return {
            "id": "summarization_chain",
            "name": "Summarization Chain",
            "type": "@n8n/n8n-nodes-langchain.chainSummarization",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "text": "={{ $json.text }}",
                "model": {
                    "modelId": f"@n8n/n8n-nodes-langchain.lmChat{model_provider.title()}",
                    "modelName": model,
                },
                "type": chain_type,
                "options": {"maxTokens": 1000},
            },
        }

    @staticmethod
    def create_conversational_retrieval_chain(
        vector_store_node_name: str, memory_node_name: str
    ) -> Dict[str, Any]:
        """Create a conversational retrieval chain"""

        return {
            "id": "conversational_retrieval",
            "name": "Conversational Retrieval",
            "type": "@n8n/n8n-nodes-langchain.chainConversationalRetrieval",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "query": "={{ $json.message }}",
                "model": {
                    "modelId": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "modelName": "gpt-4",
                },
                "vectorStore": f"={{{{ ${{{vector_store_node_name}}} }}}}",
                "memory": f"={{{{ ${{{memory_node_name}}} }}}}",
                "options": {
                    "returnSourceDocuments": True,
                    "condenseQuestionPrompt": "Given the conversation history and the new question, rephrase it as a standalone question.",
                },
            },
        }


class OutputParserBuilder:
    """Builder for output parser nodes"""

    @staticmethod
    def create_structured_output_parser(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured output parser"""

        return {
            "id": "output_parser_structured",
            "name": "Structured Output Parser",
            "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {"schema": schema, "inputText": "={{ $json.ai_output }}"},
        }

    @staticmethod
    def create_json_output_parser() -> Dict[str, Any]:
        """Create a JSON output parser"""

        return {
            "id": "output_parser_json",
            "name": "JSON Output Parser",
            "type": "@n8n/n8n-nodes-langchain.outputParserJson",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {"inputText": "={{ $json.ai_output }}"},
        }


def create_multi_agent_workflow(
    agents: List[Dict[str, Any]], coordinator_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a multi-agent workflow with coordination"""

    nodes = []
    connections = {}

    # Create coordinator if specified
    if coordinator_config:
        coordinator = AgentNodeBuilder.create_plan_execute_agent(
            name="Coordinator",
            objective=coordinator_config.get("objective", "Coordinate agent tasks"),
        )
        coordinator["position"] = [400, 100]
        nodes.append(coordinator)

    # Add agents
    y_position = 300
    for i, agent_config in enumerate(agents):
        agent = AgentNodeBuilder.create_conversational_agent(**agent_config)
        agent["position"] = [600, y_position + (i * 200)]
        nodes.append(agent)

        # Connect coordinator to agents
        if coordinator_config:
            if coordinator["name"] not in connections:
                connections[coordinator["name"]] = {"main": [[]]}
            connections[coordinator["name"]]["main"][0].append(
                {"node": agent["name"], "type": "main", "index": 0}
            )

    return {"nodes": nodes, "connections": connections}
