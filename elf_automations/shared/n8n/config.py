"""
N8N Workflow Configuration

Default preferences and settings for workflow generation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ServicePreferences:
    """Service preferences for workflow generation"""

    # Email preferences
    email_provider: str = "gmail"  # gmail, smtp, outlook
    email_default_from: Optional[str] = None

    # SMS preferences
    sms_provider: str = "twilio"  # twilio, mcp_sms, vonage
    sms_default_from: Optional[str] = None

    # Storage preferences
    primary_database: str = "supabase"  # supabase, postgres, mysql
    file_storage: str = "minio"  # minio, s3, local
    spreadsheet_provider: str = "google_sheets"  # google_sheets, excel_online

    # Communication preferences
    chat_platform: str = "slack"  # slack, teams, discord
    default_notification_channel: str = "#general"

    # AI preferences
    ai_provider: str = "openai"  # openai, anthropic, gemini
    ai_model: str = "gpt-4"
    ai_temperature: float = 0.7

    # MCP preferences
    mcp_enabled: bool = True
    preferred_mcp_servers: List[str] = None

    def __post_init__(self):
        if self.preferred_mcp_servers is None:
            self.preferred_mcp_servers = []


@dataclass
class NotificationSettings:
    """Notification settings by priority level"""

    high_priority: List[str] = None  # ["slack", "sms", "email"]
    medium_priority: List[str] = None  # ["slack", "email"]
    low_priority: List[str] = None  # ["email"]

    error_notifications: List[str] = None  # ["slack", "email"]
    success_notifications: List[str] = None  # ["slack"]

    def __post_init__(self):
        if self.high_priority is None:
            self.high_priority = ["slack", "sms", "email"]
        if self.medium_priority is None:
            self.medium_priority = ["slack", "email"]
        if self.low_priority is None:
            self.low_priority = ["email"]
        if self.error_notifications is None:
            self.error_notifications = ["slack", "email"]
        if self.success_notifications is None:
            self.success_notifications = ["slack"]


@dataclass
class WorkflowDefaults:
    """Default workflow settings"""

    # Execution settings
    save_execution_data: bool = True
    retry_on_fail: bool = True
    retry_count: int = 3
    retry_delay: int = 5000  # milliseconds
    timeout: int = 300  # seconds

    # Error handling
    error_workflow: Optional[str] = "error-handler"
    continue_on_fail: bool = False

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_max: int = 100
    rate_limit_window: int = 60  # seconds

    # Data handling
    batch_size: int = 100
    parallel_processing: bool = True
    max_parallel: int = 5


@dataclass
class TeamConfiguration:
    """Team-specific workflow configuration"""

    team_name: str
    preferences: ServicePreferences
    notifications: NotificationSettings
    defaults: WorkflowDefaults

    # Team-specific overrides
    custom_node_mappings: Dict[str, str] = None
    restricted_services: List[str] = None
    required_approvers: List[str] = None

    def __post_init__(self):
        if self.custom_node_mappings is None:
            self.custom_node_mappings = {}
        if self.restricted_services is None:
            self.restricted_services = []
        if self.required_approvers is None:
            self.required_approvers = []


class WorkflowConfig:
    """Global workflow configuration manager"""

    _instance = None
    _team_configs: Dict[str, TeamConfiguration] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WorkflowConfig, cls).__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance

    def _initialize_defaults(self):
        """Initialize with default configuration"""
        self.global_preferences = ServicePreferences()
        self.global_notifications = NotificationSettings()
        self.global_defaults = WorkflowDefaults()

    def get_team_config(self, team_name: str) -> TeamConfiguration:
        """Get configuration for a specific team"""
        if team_name in self._team_configs:
            return self._team_configs[team_name]

        # Return default configuration
        return TeamConfiguration(
            team_name=team_name,
            preferences=self.global_preferences,
            notifications=self.global_notifications,
            defaults=self.global_defaults,
        )

    def set_team_config(self, config: TeamConfiguration):
        """Set configuration for a specific team"""
        self._team_configs[config.team_name] = config

    def get_node_type(self, service: str, team_name: Optional[str] = None) -> str:
        """Get the appropriate node type for a service"""

        # Check team-specific mappings first
        if team_name:
            team_config = self.get_team_config(team_name)
            if service in team_config.custom_node_mappings:
                return team_config.custom_node_mappings[service]

        # Default node mappings
        node_mappings = {
            "email": f"n8n-nodes-base.{self.global_preferences.email_provider}",
            "sms": f"n8n-nodes-base.{self.global_preferences.sms_provider}",
            "database": f"n8n-nodes-base.{self.global_preferences.primary_database}",
            "spreadsheet": f"n8n-nodes-base.{self.global_preferences.spreadsheet_provider}",
            "chat": f"n8n-nodes-base.{self.global_preferences.chat_platform}",
            "ai": f"n8n-nodes-base.{self.global_preferences.ai_provider}",
        }

        return node_mappings.get(service, f"n8n-nodes-base.{service}")

    def get_notification_channels(
        self, priority: str, team_name: Optional[str] = None
    ) -> List[str]:
        """Get notification channels for a given priority"""

        config = self.get_team_config(team_name) if team_name else None
        notifications = config.notifications if config else self.global_notifications

        priority_map = {
            "high": notifications.high_priority,
            "medium": notifications.medium_priority,
            "low": notifications.low_priority,
            "error": notifications.error_notifications,
            "success": notifications.success_notifications,
        }

        return priority_map.get(priority, notifications.medium_priority)

    def is_service_allowed(self, service: str, team_name: str) -> bool:
        """Check if a service is allowed for a team"""
        team_config = self.get_team_config(team_name)
        return service not in team_config.restricted_services

    def to_dict(self) -> Dict:
        """Export configuration as dictionary"""
        return {
            "global": {
                "preferences": self.global_preferences.__dict__,
                "notifications": self.global_notifications.__dict__,
                "defaults": self.global_defaults.__dict__,
            },
            "teams": {
                name: {
                    "preferences": config.preferences.__dict__,
                    "notifications": config.notifications.__dict__,
                    "defaults": config.defaults.__dict__,
                    "custom_mappings": config.custom_node_mappings,
                    "restrictions": config.restricted_services,
                }
                for name, config in self._team_configs.items()
            },
        }


# Example team configurations
def create_marketing_team_config() -> TeamConfiguration:
    """Create configuration for marketing team"""
    preferences = ServicePreferences(
        email_provider="gmail",
        sms_provider="twilio",
        primary_database="supabase",
        chat_platform="slack",
        ai_provider="openai",
    )

    notifications = NotificationSettings(
        high_priority=["slack", "email"],
        medium_priority=["email"],
        error_notifications=["slack"],
    )

    return TeamConfiguration(
        team_name="marketing",
        preferences=preferences,
        notifications=notifications,
        defaults=WorkflowDefaults(),
        restricted_services=["direct_database_access"],
    )


def create_engineering_team_config() -> TeamConfiguration:
    """Create configuration for engineering team"""
    preferences = ServicePreferences(
        email_provider="smtp",
        primary_database="postgres",
        chat_platform="slack",
        ai_provider="anthropic",
        mcp_enabled=True,
        preferred_mcp_servers=["github", "jira", "datadog"],
    )

    notifications = NotificationSettings(
        high_priority=["slack", "sms"],
        error_notifications=["slack", "email", "pagerduty"],
    )

    defaults = WorkflowDefaults(
        retry_count=5, timeout=600, parallel_processing=True, max_parallel=10
    )

    return TeamConfiguration(
        team_name="engineering",
        preferences=preferences,
        notifications=notifications,
        defaults=defaults,
    )
