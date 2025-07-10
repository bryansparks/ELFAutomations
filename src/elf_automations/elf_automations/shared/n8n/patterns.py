"""
N8N Workflow Design Patterns

Common patterns for workflow generation with intelligent service selection.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class InputSource(Enum):
    """Available input sources for workflows"""

    WEBHOOK = "webhook"
    EMAIL_GMAIL = "email_gmail"
    EMAIL_IMAP = "email_imap"
    SMS_TWILIO = "sms_twilio"
    SMS_MCP = "sms_mcp"
    SLACK = "slack"
    GOOGLE_SHEETS = "google_sheets"
    SCHEDULE = "schedule"
    DATABASE = "database"
    API = "api"


class StorageType(Enum):
    """Storage options for workflow data"""

    SUPABASE = "supabase"
    POSTGRES = "postgres"
    GOOGLE_SHEETS = "google_sheets"
    MINIO = "minio"
    LOCAL_FILE = "local_file"
    MEMORY = "memory"


class OutputChannel(Enum):
    """Output channels for workflow results"""

    EMAIL_GMAIL = "email_gmail"
    EMAIL_SMTP = "email_smtp"
    SMS_TWILIO = "sms_twilio"
    SMS_MCP = "sms_mcp"
    SLACK = "slack"
    GOOGLE_DOCS = "google_docs"
    WEBHOOK_RESPONSE = "webhook_response"
    API_RESPONSE = "api_response"
    DATABASE = "database"


@dataclass
class WorkflowPattern:
    """Base class for workflow patterns"""

    name: str
    description: str
    inputs: List[InputSource]
    storage: List[StorageType]
    outputs: List[OutputChannel]
    requires_ai: bool = False
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputs": [inp.value for inp in self.inputs],
            "storage": [stor.value for stor in self.storage],
            "outputs": [out.value for out in self.outputs],
            "requires_ai": self.requires_ai,
            "requires_approval": self.requires_approval,
        }


class WorkflowPatterns:
    """Collection of common workflow patterns"""

    @staticmethod
    def input_process_output() -> WorkflowPattern:
        """Basic input-process-output pattern"""
        return WorkflowPattern(
            name="input_process_output",
            description="Receive data, process it, and send to destination",
            inputs=[InputSource.WEBHOOK, InputSource.API],
            storage=[StorageType.MEMORY],
            outputs=[OutputChannel.API_RESPONSE, OutputChannel.DATABASE],
        )

    @staticmethod
    def email_management() -> WorkflowPattern:
        """Email triage and response pattern"""
        return WorkflowPattern(
            name="email_management",
            description="Monitor emails, categorize, and route appropriately",
            inputs=[InputSource.EMAIL_GMAIL, InputSource.EMAIL_IMAP],
            storage=[StorageType.SUPABASE],
            outputs=[OutputChannel.EMAIL_GMAIL, OutputChannel.SLACK],
            requires_ai=True,
        )

    @staticmethod
    def sms_communication() -> WorkflowPattern:
        """SMS communication hub pattern"""
        return WorkflowPattern(
            name="sms_communication",
            description="Handle incoming SMS, process, and respond",
            inputs=[InputSource.SMS_TWILIO, InputSource.SMS_MCP],
            storage=[StorageType.SUPABASE],
            outputs=[OutputChannel.SMS_TWILIO, OutputChannel.SLACK],
            requires_ai=True,
        )

    @staticmethod
    def approval_workflow() -> WorkflowPattern:
        """Multi-level approval pattern"""
        return WorkflowPattern(
            name="approval_workflow",
            description="Route requests through approval chain",
            inputs=[InputSource.WEBHOOK, InputSource.SLACK],
            storage=[StorageType.SUPABASE],
            outputs=[OutputChannel.SLACK, OutputChannel.EMAIL_GMAIL],
            requires_approval=True,
        )

    @staticmethod
    def data_pipeline() -> WorkflowPattern:
        """ETL data pipeline pattern"""
        return WorkflowPattern(
            name="data_pipeline",
            description="Extract, transform, and load data",
            inputs=[InputSource.DATABASE, InputSource.API, InputSource.GOOGLE_SHEETS],
            storage=[StorageType.SUPABASE, StorageType.GOOGLE_SHEETS],
            outputs=[OutputChannel.DATABASE, OutputChannel.SLACK],
        )

    @staticmethod
    def report_generation() -> WorkflowPattern:
        """Automated report generation pattern"""
        return WorkflowPattern(
            name="report_generation",
            description="Generate and distribute reports",
            inputs=[InputSource.SCHEDULE, InputSource.DATABASE],
            storage=[StorageType.GOOGLE_SHEETS, StorageType.MINIO],
            outputs=[
                OutputChannel.EMAIL_GMAIL,
                OutputChannel.GOOGLE_DOCS,
                OutputChannel.SLACK,
            ],
        )

    @staticmethod
    def customer_support() -> WorkflowPattern:
        """Multi-channel customer support pattern"""
        return WorkflowPattern(
            name="customer_support",
            description="Unified support across email, SMS, and chat",
            inputs=[InputSource.EMAIL_GMAIL, InputSource.SMS_TWILIO, InputSource.SLACK],
            storage=[StorageType.SUPABASE],
            outputs=[
                OutputChannel.EMAIL_GMAIL,
                OutputChannel.SMS_TWILIO,
                OutputChannel.SLACK,
            ],
            requires_ai=True,
        )

    @staticmethod
    def data_collection() -> WorkflowPattern:
        """Form and survey data collection pattern"""
        return WorkflowPattern(
            name="data_collection",
            description="Collect data from forms and surveys",
            inputs=[InputSource.WEBHOOK, InputSource.GOOGLE_SHEETS],
            storage=[StorageType.SUPABASE, StorageType.GOOGLE_SHEETS],
            outputs=[OutputChannel.EMAIL_GMAIL, OutputChannel.GOOGLE_DOCS],
        )


class NodeMapper:
    """Maps pattern components to n8n node types"""

    INPUT_NODE_MAP = {
        InputSource.WEBHOOK: {
            "type": "n8n-nodes-base.webhook",
            "config": {"httpMethod": "POST", "responseMode": "responseNode"},
        },
        InputSource.EMAIL_GMAIL: {
            "type": "n8n-nodes-base.gmail",
            "config": {
                "operation": "getAll",
                "filters": {"labelIds": ["INBOX", "UNREAD"]},
            },
        },
        InputSource.EMAIL_IMAP: {
            "type": "n8n-nodes-base.emailReadImap",
            "config": {"mailbox": "INBOX", "format": "resolved"},
        },
        InputSource.SMS_TWILIO: {
            "type": "n8n-nodes-base.twilio",
            "config": {"operation": "receive"},
        },
        InputSource.SMS_MCP: {
            "type": "n8n-nodes-langchain.toolMcp",
            "config": {"tool": "sms_receiver"},
        },
        InputSource.SLACK: {
            "type": "n8n-nodes-base.slack",
            "config": {"operation": "message", "resource": "message"},
        },
        InputSource.GOOGLE_SHEETS: {
            "type": "n8n-nodes-base.googleSheets",
            "config": {"operation": "read", "options": {}},
        },
        InputSource.SCHEDULE: {
            "type": "n8n-nodes-base.scheduleTrigger",
            "config": {"rule": {"interval": [{"field": "hours", "intervalValue": 1}]}},
        },
        InputSource.DATABASE: {
            "type": "n8n-nodes-base.postgres",
            "config": {"operation": "select"},
        },
        InputSource.API: {
            "type": "n8n-nodes-base.httpRequest",
            "config": {"method": "GET"},
        },
    }

    STORAGE_NODE_MAP = {
        StorageType.SUPABASE: {
            "type": "n8n-nodes-base.supabase",
            "config": {"operation": "insert"},
        },
        StorageType.POSTGRES: {
            "type": "n8n-nodes-base.postgres",
            "config": {"operation": "insert"},
        },
        StorageType.GOOGLE_SHEETS: {
            "type": "n8n-nodes-base.googleSheets",
            "config": {"operation": "append"},
        },
        StorageType.MINIO: {
            "type": "n8n-nodes-base.httpRequest",
            "config": {"method": "PUT", "url": "={{$env.MINIO_URL}}/bucket/object"},
        },
    }

    OUTPUT_NODE_MAP = {
        OutputChannel.EMAIL_GMAIL: {
            "type": "n8n-nodes-base.gmail",
            "config": {"operation": "send"},
        },
        OutputChannel.EMAIL_SMTP: {
            "type": "n8n-nodes-base.emailSend",
            "config": {"options": {}},
        },
        OutputChannel.SMS_TWILIO: {
            "type": "n8n-nodes-base.twilio",
            "config": {"operation": "send"},
        },
        OutputChannel.SMS_MCP: {
            "type": "n8n-nodes-langchain.toolMcp",
            "config": {"tool": "sms_sender"},
        },
        OutputChannel.SLACK: {
            "type": "n8n-nodes-base.slack",
            "config": {"operation": "post", "channel": "#general"},
        },
        OutputChannel.GOOGLE_DOCS: {
            "type": "n8n-nodes-base.googleDocs",
            "config": {"operation": "create"},
        },
        OutputChannel.WEBHOOK_RESPONSE: {
            "type": "n8n-nodes-base.respondToWebhook",
            "config": {"respondWith": "json"},
        },
        OutputChannel.DATABASE: {
            "type": "n8n-nodes-base.postgres",
            "config": {"operation": "insert"},
        },
    }

    @classmethod
    def get_node_config(cls, component_type: str, component: Enum) -> Dict[str, Any]:
        """Get node configuration for a pattern component"""
        if component_type == "input" and isinstance(component, InputSource):
            return cls.INPUT_NODE_MAP.get(component, {})
        elif component_type == "storage" and isinstance(component, StorageType):
            return cls.STORAGE_NODE_MAP.get(component, {})
        elif component_type == "output" and isinstance(component, OutputChannel):
            return cls.OUTPUT_NODE_MAP.get(component, {})
        return {}


def detect_pattern(description: str) -> Optional[WorkflowPattern]:
    """Detect which pattern best matches the description"""

    description_lower = description.lower()

    # Email management keywords
    if any(word in description_lower for word in ["email", "gmail", "inbox", "triage"]):
        return WorkflowPatterns.email_management()

    # SMS/Text keywords
    if any(word in description_lower for word in ["sms", "text", "twilio", "message"]):
        return WorkflowPatterns.sms_communication()

    # Approval keywords
    if any(
        word in description_lower
        for word in ["approval", "approve", "escalate", "authorize"]
    ):
        return WorkflowPatterns.approval_workflow()

    # Data pipeline keywords
    if any(
        word in description_lower
        for word in ["etl", "pipeline", "extract", "transform", "migrate"]
    ):
        return WorkflowPatterns.data_pipeline()

    # Report keywords
    if any(
        word in description_lower
        for word in ["report", "summary", "dashboard", "analytics"]
    ):
        return WorkflowPatterns.report_generation()

    # Support keywords
    if any(
        word in description_lower
        for word in ["support", "help", "ticket", "customer service"]
    ):
        return WorkflowPatterns.customer_support()

    # Form/Survey keywords
    if any(
        word in description_lower
        for word in ["form", "survey", "collect", "submission"]
    ):
        return WorkflowPatterns.data_collection()

    # Default pattern
    return WorkflowPatterns.input_process_output()


def generate_pattern_nodes(
    pattern: WorkflowPattern, config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate n8n nodes based on a pattern and configuration"""

    nodes = []
    node_id = 1
    y_position = 300
    x_position = 250

    # Input nodes
    for i, input_source in enumerate(pattern.inputs):
        node_config = NodeMapper.get_node_config("input", input_source)
        if node_config:
            node = {
                "id": f"input_{node_id}",
                "name": f"{input_source.value.replace('_', ' ').title()} Input",
                "type": node_config["type"],
                "position": [x_position, y_position + (i * 150)],
                "parameters": node_config.get("config", {}),
            }
            nodes.append(node)
            node_id += 1

    x_position += 200

    # Processing nodes (if AI required)
    if pattern.requires_ai:
        ai_node = {
            "id": f"ai_process_{node_id}",
            "name": "AI Processing",
            "type": "n8n-nodes-base.openAi",
            "position": [x_position, y_position],
            "parameters": {
                "operation": "message",
                "modelId": "gpt-4",
                "messages": {
                    "values": [{"content": "Process and analyze the input data"}]
                },
            },
        }
        nodes.append(ai_node)
        node_id += 1
        x_position += 200

    # Storage nodes
    for i, storage_type in enumerate(pattern.storage):
        node_config = NodeMapper.get_node_config("storage", storage_type)
        if node_config:
            node = {
                "id": f"storage_{node_id}",
                "name": f"Store in {storage_type.value.replace('_', ' ').title()}",
                "type": node_config["type"],
                "position": [x_position, y_position + (i * 150)],
                "parameters": node_config.get("config", {}),
            }
            nodes.append(node)
            node_id += 1

    x_position += 200

    # Output nodes
    for i, output_channel in enumerate(pattern.outputs):
        node_config = NodeMapper.get_node_config("output", output_channel)
        if node_config:
            node = {
                "id": f"output_{node_id}",
                "name": f"{output_channel.value.replace('_', ' ').title()} Output",
                "type": node_config["type"],
                "position": [x_position, y_position + (i * 150)],
                "parameters": node_config.get("config", {}),
            }
            nodes.append(node)
            node_id += 1

    return nodes
