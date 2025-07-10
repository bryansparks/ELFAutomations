"""
N8N AI Workflow Patterns

Advanced AI-powered workflow patterns based on 2024-2025 best practices.
Includes multi-agent systems, RAG patterns, and safety controls.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .patterns import InputSource, OutputChannel, StorageType, WorkflowPattern


class AIModelProvider(Enum):
    """Available AI model providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    VERTEX = "vertex"
    CUSTOM = "custom"


class AIAgentType(Enum):
    """Types of AI agents in workflows"""

    CONVERSATIONAL = "conversational"
    TOOLS = "tools"
    REACT = "react"
    PLAN_EXECUTE = "plan_execute"
    STRUCTURED_CHAT = "structured_chat"
    OPENAI_FUNCTIONS = "openai_functions"


class VectorStoreType(Enum):
    """Vector store options for RAG"""

    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    CHROMA = "chroma"
    SUPABASE = "supabase"
    MEMORY = "in_memory"


@dataclass
class AIWorkflowPattern(WorkflowPattern):
    """Extended workflow pattern for AI-specific features"""

    ai_providers: List[AIModelProvider]
    agent_types: List[AIAgentType]
    vector_stores: List[VectorStoreType] = None
    requires_memory: bool = False
    requires_tools: bool = False
    human_in_loop: bool = False
    safety_controls: List[str] = None


class AIWorkflowPatterns:
    """Collection of AI-powered workflow patterns"""

    @staticmethod
    def ai_customer_support() -> AIWorkflowPattern:
        """Multi-channel AI customer support with memory"""
        return AIWorkflowPattern(
            name="ai_customer_support",
            description="AI-powered support across email, chat, and SMS with conversation memory",
            inputs=[InputSource.EMAIL_GMAIL, InputSource.SLACK, InputSource.SMS_TWILIO],
            storage=[StorageType.SUPABASE],
            outputs=[
                OutputChannel.EMAIL_GMAIL,
                OutputChannel.SLACK,
                OutputChannel.SMS_TWILIO,
            ],
            requires_ai=True,
            ai_providers=[AIModelProvider.OPENAI, AIModelProvider.ANTHROPIC],
            agent_types=[AIAgentType.CONVERSATIONAL, AIAgentType.TOOLS],
            requires_memory=True,
            requires_tools=True,
            human_in_loop=True,
            safety_controls=[
                "content_filter",
                "response_validation",
                "escalation_rules",
            ],
        )

    @staticmethod
    def document_analysis_rag() -> AIWorkflowPattern:
        """Document analysis with RAG and vector storage"""
        return AIWorkflowPattern(
            name="document_analysis_rag",
            description="Analyze documents using RAG with vector embeddings",
            inputs=[InputSource.WEBHOOK, InputSource.GOOGLE_SHEETS],
            storage=[StorageType.SUPABASE, StorageType.MINIO],
            outputs=[OutputChannel.API_RESPONSE, OutputChannel.GOOGLE_DOCS],
            requires_ai=True,
            ai_providers=[AIModelProvider.OPENAI],
            agent_types=[AIAgentType.TOOLS, AIAgentType.REACT],
            vector_stores=[VectorStoreType.PINECONE, VectorStoreType.SUPABASE],
            requires_memory=False,
            requires_tools=True,
            safety_controls=["data_validation", "pii_detection"],
        )

    @staticmethod
    def multi_agent_research() -> AIWorkflowPattern:
        """Multi-agent system for research and analysis"""
        return AIWorkflowPattern(
            name="multi_agent_research",
            description="Coordinated agents for research, analysis, and report generation",
            inputs=[InputSource.WEBHOOK, InputSource.SCHEDULE],
            storage=[StorageType.SUPABASE],
            outputs=[
                OutputChannel.EMAIL_GMAIL,
                OutputChannel.GOOGLE_DOCS,
                OutputChannel.SLACK,
            ],
            requires_ai=True,
            ai_providers=[
                AIModelProvider.OPENAI,
                AIModelProvider.ANTHROPIC,
                AIModelProvider.GOOGLE,
            ],
            agent_types=[
                AIAgentType.PLAN_EXECUTE,
                AIAgentType.TOOLS,
                AIAgentType.REACT,
            ],
            requires_memory=True,
            requires_tools=True,
            human_in_loop=True,
            safety_controls=["fact_checking", "source_validation", "output_review"],
        )

    @staticmethod
    def ai_data_analyst() -> AIWorkflowPattern:
        """AI-powered data analysis and visualization"""
        return AIWorkflowPattern(
            name="ai_data_analyst",
            description="Analyze data, generate insights, and create visualizations",
            inputs=[InputSource.DATABASE, InputSource.API, InputSource.GOOGLE_SHEETS],
            storage=[StorageType.SUPABASE],
            outputs=[
                OutputChannel.SLACK,
                OutputChannel.EMAIL_GMAIL,
                OutputChannel.GOOGLE_DOCS,
            ],
            requires_ai=True,
            ai_providers=[AIModelProvider.OPENAI],
            agent_types=[AIAgentType.TOOLS, AIAgentType.OPENAI_FUNCTIONS],
            requires_memory=False,
            requires_tools=True,
            safety_controls=["data_privacy", "calculation_validation"],
        )

    @staticmethod
    def content_generation_pipeline() -> AIWorkflowPattern:
        """Automated content creation with review process"""
        return AIWorkflowPattern(
            name="content_generation_pipeline",
            description="Generate, review, and publish content across channels",
            inputs=[InputSource.WEBHOOK, InputSource.SCHEDULE],
            storage=[StorageType.SUPABASE, StorageType.GOOGLE_SHEETS],
            outputs=[
                OutputChannel.GOOGLE_DOCS,
                OutputChannel.SLACK,
                OutputChannel.EMAIL_GMAIL,
            ],
            requires_ai=True,
            ai_providers=[AIModelProvider.OPENAI, AIModelProvider.ANTHROPIC],
            agent_types=[AIAgentType.CONVERSATIONAL, AIAgentType.TOOLS],
            requires_memory=True,
            requires_tools=False,
            human_in_loop=True,
            safety_controls=["content_review", "brand_compliance", "plagiarism_check"],
        )

    @staticmethod
    def ai_workflow_orchestrator() -> AIWorkflowPattern:
        """AI agent that creates and manages other workflows"""
        return AIWorkflowPattern(
            name="ai_workflow_orchestrator",
            description="Meta-workflow that generates and orchestrates other workflows",
            inputs=[InputSource.WEBHOOK, InputSource.SLACK],
            storage=[StorageType.SUPABASE],
            outputs=[OutputChannel.WEBHOOK_RESPONSE, OutputChannel.SLACK],
            requires_ai=True,
            ai_providers=[AIModelProvider.ANTHROPIC],
            agent_types=[AIAgentType.PLAN_EXECUTE, AIAgentType.TOOLS],
            requires_memory=True,
            requires_tools=True,
            human_in_loop=True,
            safety_controls=[
                "workflow_validation",
                "resource_limits",
                "approval_required",
            ],
        )

    @staticmethod
    def intelligent_form_processor() -> AIWorkflowPattern:
        """Process forms with AI understanding and routing"""
        return AIWorkflowPattern(
            name="intelligent_form_processor",
            description="Understand form intent and route to appropriate handlers",
            inputs=[InputSource.WEBHOOK, InputSource.EMAIL_GMAIL],
            storage=[StorageType.SUPABASE],
            outputs=[
                OutputChannel.EMAIL_GMAIL,
                OutputChannel.SLACK,
                OutputChannel.DATABASE,
            ],
            requires_ai=True,
            ai_providers=[AIModelProvider.OPENAI],
            agent_types=[AIAgentType.STRUCTURED_CHAT],
            requires_memory=False,
            requires_tools=False,
            human_in_loop=False,
            safety_controls=["input_validation", "intent_verification"],
        )

    @staticmethod
    def ai_code_reviewer() -> AIWorkflowPattern:
        """Automated code review with AI insights"""
        return AIWorkflowPattern(
            name="ai_code_reviewer",
            description="Review code changes and provide intelligent feedback",
            inputs=[InputSource.WEBHOOK],
            storage=[StorageType.SUPABASE],
            outputs=[OutputChannel.WEBHOOK_RESPONSE, OutputChannel.SLACK],
            requires_ai=True,
            ai_providers=[AIModelProvider.ANTHROPIC, AIModelProvider.OPENAI],
            agent_types=[AIAgentType.TOOLS, AIAgentType.REACT],
            requires_memory=True,
            requires_tools=True,
            safety_controls=["code_safety_check", "security_scan"],
        )


def detect_ai_pattern(
    description: str,
) -> Tuple[Optional[AIWorkflowPattern], Dict[str, Any]]:
    """Detect AI workflow pattern and extract configuration"""

    description_lower = description.lower()

    # Customer support keywords
    if any(
        word in description_lower
        for word in ["support", "help desk", "customer service", "chat support"]
    ):
        pattern = AIWorkflowPatterns.ai_customer_support()

    # Document/RAG keywords
    elif any(
        word in description_lower
        for word in ["document", "rag", "embedding", "vector", "knowledge base"]
    ):
        pattern = AIWorkflowPatterns.document_analysis_rag()

    # Research keywords
    elif any(
        word in description_lower
        for word in ["research", "investigate", "analyze multiple", "multi-agent"]
    ):
        pattern = AIWorkflowPatterns.multi_agent_research()

    # Data analysis keywords
    elif any(
        word in description_lower
        for word in ["data analysis", "analytics", "insights", "visualization"]
    ):
        pattern = AIWorkflowPatterns.ai_data_analyst()

    # Content generation keywords
    elif any(
        word in description_lower
        for word in ["content", "article", "blog", "generate text", "write"]
    ):
        pattern = AIWorkflowPatterns.content_generation_pipeline()

    # Workflow orchestration keywords
    elif any(
        word in description_lower
        for word in ["orchestrate", "meta", "workflow generator", "automation creator"]
    ):
        pattern = AIWorkflowPatterns.ai_workflow_orchestrator()

    # Form processing keywords
    elif any(
        word in description_lower
        for word in ["form", "submission", "intake", "application"]
    ):
        pattern = AIWorkflowPatterns.intelligent_form_processor()

    # Code review keywords
    elif any(
        word in description_lower
        for word in ["code review", "pull request", "code analysis"]
    ):
        pattern = AIWorkflowPatterns.ai_code_reviewer()

    else:
        return None, {}

    # Extract specific requirements
    config = {
        "pattern": pattern.name,
        "detected_features": {
            "needs_memory": "memory" in description_lower
            or "remember" in description_lower,
            "needs_human_approval": "approval" in description_lower
            or "review" in description_lower,
            "needs_vector_store": "vector" in description_lower
            or "embedding" in description_lower,
            "needs_multiple_agents": "multi" in description_lower
            or "team" in description_lower,
        },
        "suggested_models": {
            "primary": "gpt-4" if "complex" in description_lower else "gpt-3.5-turbo",
            "fallback": "claude-3-sonnet",
        },
        "safety_requirements": extract_safety_requirements(description),
    }

    return pattern, config


def extract_safety_requirements(description: str) -> List[str]:
    """Extract safety and compliance requirements from description"""

    requirements = []
    description_lower = description.lower()

    if any(
        word in description_lower for word in ["pii", "personal", "private", "gdpr"]
    ):
        requirements.append("pii_protection")

    if any(word in description_lower for word in ["approve", "review", "check"]):
        requirements.append("human_review")

    if any(word in description_lower for word in ["limit", "quota", "budget"]):
        requirements.append("rate_limiting")

    if any(word in description_lower for word in ["validate", "verify", "accurate"]):
        requirements.append("output_validation")

    if any(word in description_lower for word in ["secure", "safety", "safe"]):
        requirements.append("security_checks")

    return requirements


class AINodeConfiguration:
    """Configuration templates for AI nodes"""

    @staticmethod
    def create_agent_node(
        agent_type: AIAgentType,
        provider: AIModelProvider,
        model: str = None,
        temperature: float = 0.7,
        tools: List[str] = None,
        memory_key: str = None,
    ) -> Dict[str, Any]:
        """Create an AI agent node configuration"""

        base_config = {
            "type": "n8n-nodes-langchain.agent",
            "typeVersion": 1,
            "parameters": {
                "agentType": agent_type.value,
                "promptType": "auto",
                "text": "={{ $json.query }}",
                "options": {
                    "temperature": temperature,
                    "maxIterations": 10,
                },
            },
        }

        # Add model configuration
        if provider == AIModelProvider.OPENAI:
            base_config["parameters"]["options"]["model"] = model or "gpt-4"
        elif provider == AIModelProvider.ANTHROPIC:
            base_config["parameters"]["options"]["model"] = (
                model or "claude-3-sonnet-20240229"
            )

        # Add tools if specified
        if tools:
            base_config["parameters"]["tools"] = tools

        # Add memory if specified
        if memory_key:
            base_config["parameters"]["options"][
                "sessionId"
            ] = f"={{{{ $json.{memory_key} }}}}"
            base_config["parameters"]["options"]["memoryKey"] = "chat_history"

        return base_config

    @staticmethod
    def create_vector_store_node(
        store_type: VectorStoreType,
        operation: str = "search",
        embedding_model: str = "text-embedding-ada-002",
    ) -> Dict[str, Any]:
        """Create a vector store node configuration"""

        if store_type == VectorStoreType.PINECONE:
            return {
                "type": "n8n-nodes-langchain.vectorStorePinecone",
                "typeVersion": 1,
                "parameters": {
                    "operation": operation,
                    "index": "{{ $json.index_name }}",
                    "options": {
                        "embeddingModel": embedding_model,
                    },
                },
            }
        elif store_type == VectorStoreType.SUPABASE:
            return {
                "type": "n8n-nodes-langchain.vectorStoreSupabase",
                "typeVersion": 1,
                "parameters": {
                    "operation": operation,
                    "tableName": "embeddings",
                    "options": {
                        "embeddingModel": embedding_model,
                    },
                },
            }
        else:
            # Default in-memory store
            return {
                "type": "n8n-nodes-langchain.vectorStoreMemory",
                "typeVersion": 1,
                "parameters": {
                    "operation": operation,
                },
            }

    @staticmethod
    def create_tool_node(tool_type: str) -> Dict[str, Any]:
        """Create a tool node for AI agents"""

        tool_configs = {
            "calculator": {
                "type": "n8n-nodes-langchain.toolCalculator",
                "typeVersion": 1,
                "parameters": {},
            },
            "code_executor": {
                "type": "n8n-nodes-langchain.toolCode",
                "typeVersion": 1,
                "parameters": {
                    "language": "javascript",
                    "code": "// Process input\nreturn items;",
                },
            },
            "web_search": {
                "type": "n8n-nodes-langchain.toolGoogleSearch",
                "typeVersion": 1,
                "parameters": {"query": "={{ $json.search_query }}"},
            },
            "sql_query": {
                "type": "n8n-nodes-langchain.toolSqlQuery",
                "typeVersion": 1,
                "parameters": {
                    "query": "={{ $json.sql_query }}",
                    "database": "postgres",
                },
            },
            "mcp": {
                "type": "n8n-nodes-langchain.toolMcp",
                "typeVersion": 1,
                "parameters": {
                    "server": "{{ $json.mcp_server }}",
                    "tool": "{{ $json.mcp_tool }}",
                },
            },
        }

        return tool_configs.get(tool_type, tool_configs["code_executor"])

    @staticmethod
    def create_memory_node(memory_type: str = "buffer") -> Dict[str, Any]:
        """Create a memory node for conversational AI"""

        memory_configs = {
            "buffer": {
                "type": "n8n-nodes-langchain.memoryBufferMemory",
                "typeVersion": 1,
                "parameters": {
                    "sessionId": "={{ $json.session_id }}",
                    "memoryKey": "chat_history",
                },
            },
            "window": {
                "type": "n8n-nodes-langchain.memoryBufferWindowMemory",
                "typeVersion": 1,
                "parameters": {
                    "sessionId": "={{ $json.session_id }}",
                    "memoryKey": "chat_history",
                    "windowSize": 10,
                },
            },
            "summary": {
                "type": "n8n-nodes-langchain.memorySummaryMemory",
                "typeVersion": 1,
                "parameters": {
                    "sessionId": "={{ $json.session_id }}",
                    "memoryKey": "chat_history",
                    "aiModel": "gpt-3.5-turbo",
                },
            },
        }

        return memory_configs.get(memory_type, memory_configs["buffer"])

    @staticmethod
    def create_safety_node(safety_type: str) -> Dict[str, Any]:
        """Create a safety/validation node"""

        safety_configs = {
            "content_filter": {
                "type": "n8n-nodes-base.if",
                "typeVersion": 1,
                "parameters": {
                    "conditions": {
                        "string": [
                            {
                                "value1": "={{ $json.content }}",
                                "operation": "notContains",
                                "value2": "inappropriate",
                            }
                        ]
                    }
                },
            },
            "pii_detection": {
                "type": "n8n-nodes-base.code",
                "typeVersion": 1,
                "parameters": {
                    "jsCode": """
// PII detection logic
const text = $input.first().json.content;
const piiPatterns = {
    ssn: /\\b\\d{3}-\\d{2}-\\d{4}\\b/,
    creditCard: /\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b/,
    email: /\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/
};

const detected = Object.keys(piiPatterns).filter(key =>
    piiPatterns[key].test(text)
);

return [{
    json: {
        hasPII: detected.length > 0,
        types: detected,
        content: text
    }
}];"""
                },
            },
            "rate_limiter": {
                "type": "n8n-nodes-base.code",
                "typeVersion": 1,
                "parameters": {
                    "jsCode": """
// Rate limiting logic
const userId = $input.first().json.user_id;
const now = Date.now();
const limit = 100; // requests per hour

// This would normally check a database
// For demo, we'll pass through
return [{
    json: {
        allowed: true,
        userId: userId,
        timestamp: now
    }
}];"""
                },
            },
            "human_approval": {
                "type": "n8n-nodes-base.wait",
                "typeVersion": 1,
                "parameters": {
                    "resume": "webhook",
                    "options": {"webhookSuffix": "/approve/{{ $json.request_id }}"},
                },
            },
        }

        return safety_configs.get(safety_type, safety_configs["content_filter"])
