#!/usr/bin/env python3
"""
Integration script to add conversation logging to team agents
This modifies the generated agent files to include logging capabilities
"""

import os
from pathlib import Path


def create_logging_integration_template():
    """Generate template code for adding logging to agents"""

    crewai_logging_template = '''
# Add this import at the top of each agent file
from tools.conversation_logging_system import ConversationLogger, MessageType

# Add to __init__ method after self.agent initialization:
        # Initialize conversation logger
        self.conversation_logger = ConversationLogger("{team_name}")
        self.team_name = "{team_name}"

# Add these methods to the agent class:
    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a proposal message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata
        )

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a challenge/skeptical message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata
        )

    def log_decision(self, message: str, **metadata):
        """Log a decision message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.DECISION,
            metadata=metadata
        )

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a general update message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata
        )

# Override or extend execute method to add logging:
    def execute_with_logging(self, task):
        """Execute task with conversation logging"""
        task_id = getattr(task, 'id', f"task_{datetime.now().timestamp()}")

        with self.conversation_logger.log_task(task_id, str(task)):
            # Log task start
            self.log_update(f"Starting task: {task}")

            # Execute the actual task
            result = self.agent.execute(task)

            # Log completion
            self.log_update(f"Completed task with result: {result}")

            return result
'''

    langgraph_logging_template = '''
# Add this import at the top
from tools.conversation_logging_system import ConversationLogger, MessageType

# Add to __init__ method:
        # Initialize conversation logger
        self.conversation_logger = ConversationLogger("{team_name}")

# Modify state update methods to include logging:
    def _process_message_with_logging(self, state: Dict, message: BaseMessage) -> Dict:
        """Process a message and log the conversation"""

        # Extract sender info from message metadata
        sender = message.additional_kwargs.get('sender', self.name)
        message_type = message.additional_kwargs.get('type', MessageType.UPDATE)

        # Log the message
        self.conversation_logger.log_message(
            agent_name=sender,
            message=message.content,
            message_type=message_type,
            metadata={
                'state_id': state.get('agent_id'),
                'task': state.get('current_task')
            }
        )

        # Continue with normal processing
        return self._process_message(state, message)
'''

    crew_py_logging_template = '''
# Add to crew.py for task execution logging

from tools.conversation_logging_system import ConversationLogger

class {team_class_name}:
    def __init__(self):
        # ... existing init code ...
        self.conversation_logger = ConversationLogger("{team_name}")

    def kickoff(self, inputs: Optional[Dict] = None) -> Any:
        """Execute the crew with conversation logging"""

        task_id = f"crew_task_{datetime.now().timestamp()}"
        task_description = inputs.get('task', 'Crew execution') if inputs else 'Crew execution'

        self.conversation_logger.start_conversation(task_id, task_description)

        try:
            # Execute crew
            result = self.crew.kickoff(inputs=inputs)

            # Log successful completion
            self.conversation_logger.log_message(
                "crew_manager",
                f"Crew completed successfully: {result}",
                MessageType.DECISION
            )

            self.conversation_logger.end_conversation("completed")
            return result

        except Exception as e:
            # Log failure
            self.conversation_logger.log_message(
                "crew_manager",
                f"Crew failed with error: {str(e)}",
                MessageType.UPDATE
            )

            self.conversation_logger.end_conversation(f"failed: {str(e)}")
            raise
'''

    return {
        "crewai": crewai_logging_template,
        "langgraph": langgraph_logging_template,
        "crew": crew_py_logging_template,
    }


def add_logging_to_team_factory():
    """
    Modify team_factory.py to automatically include logging in generated agents
    """

    modifications = '''
# In _generate_crewai_agents method, after the agent class definition, add:

# Insert logging imports
agent_content = agent_content.replace(
    'from typing import Optional, List, Dict, Any',
    'from typing import Optional, List, Dict, Any\\nfrom tools.conversation_logging_system import ConversationLogger, MessageType\\nfrom datetime import datetime'
)

# Add logging initialization in __init__
init_addition = """
        # Initialize conversation logger
        self.conversation_logger = ConversationLogger("{}")
        self.team_name = "{}"
""".format(team_spec.name, team_spec.name)

agent_content = agent_content.replace(
    'self.agent = self._create_agent()',
    f'self.agent = self._create_agent()\\n{init_addition}'
)

# Add logging methods before the file write
logging_methods = """
    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        \"\"\"Log a proposal message\"\"\"
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata
        )

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        \"\"\"Log a challenge/skeptical message\"\"\"
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata
        )

    def log_decision(self, message: str, **metadata):
        \"\"\"Log a decision message\"\"\"
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.DECISION,
            metadata=metadata
        )

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        \"\"\"Log a general update message\"\"\"
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata
        )

    def execute_with_logging(self, task):
        \"\"\"Execute task with conversation logging\"\"\"
        task_id = getattr(task, 'id', f"task_{datetime.now().timestamp()}")

        with self.conversation_logger.log_task(task_id, str(task)):
            # Log task start
            self.log_update(f"Starting task: {task}")

            # Execute the actual task
            result = self.agent.execute(task)

            # Log completion
            self.log_update(f"Completed task with result: {result}")

            return result
"""

# Insert logging methods before the closing of the class
agent_content = agent_content.rstrip()  # Remove trailing whitespace
if agent_content.endswith('"""'):
    # If ends with docstring, add methods after
    agent_content += logging_methods
else:
    # Otherwise add before the last line
    agent_content += '\\n' + logging_methods
'''

    return modifications


def create_setup_logging_script():
    """Create a script to set up conversation logging in Supabase"""

    setup_script = '''#!/usr/bin/env python3
"""
Setup script for conversation logging in Supabase
Run this once to create the necessary tables and views
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client
from tools.conversation_logging_system import SUPABASE_SCHEMA


def setup_conversation_logging():
    """Create tables and views for conversation logging"""

    print("Setting up conversation logging in Supabase...")

    try:
        client = get_supabase_client()

        # Execute the schema SQL
        # Note: Supabase Python client doesn't support direct SQL execution
        # You'll need to run this SQL in the Supabase dashboard or use psycopg2

        print("\\nPlease run the following SQL in your Supabase dashboard:\\n")
        print(SUPABASE_SCHEMA)

        print("\\n✅ Setup instructions displayed!")
        print("\\nAfter creating the tables, your teams will automatically log conversations to Supabase.")

    except Exception as e:
        print(f"Error: {e}")
        print("\\nMake sure your Supabase credentials are configured in .env")


if __name__ == "__main__":
    setup_conversation_logging()
'''

    return setup_script


def create_example_logged_agent():
    """Create an example agent that demonstrates logging usage"""

    example_agent = '''#!/usr/bin/env python3
"""
Example agent with comprehensive conversation logging
Shows best practices for logging team conversations
"""

from crewai import Agent, Task
from typing import Optional, List, Dict, Any
from tools.conversation_logging_system import ConversationLogger, MessageType
from datetime import datetime
import time


class MarketingManagerWithLogging:
    """Marketing Manager with full conversation logging"""

    def __init__(self, tools: Optional[List] = None):
        self.role = "Marketing Manager"
        self.team_name = "marketing-team"
        self.conversation_logger = ConversationLogger(self.team_name)
        self.tools = tools or []

        # Create the CrewAI agent
        self.agent = Agent(
            role=self.role,
            goal="Drive marketing strategy and team coordination",
            backstory="Experienced marketing leader with data-driven approach",
            tools=self.tools,
            verbose=True
        )

    def analyze_campaign_request(self, campaign_brief: str) -> Dict:
        """Analyze a campaign request with full logging"""

        task_id = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with self.conversation_logger.log_task(task_id, f"Analyze campaign: {campaign_brief[:50]}..."):

            # Initial thoughts
            self.log_update("Reviewing campaign brief and objectives")
            time.sleep(0.5)  # Simulate thinking

            # Ask for data
            self.log_update(
                "I need last quarter's performance data to inform this campaign",
                to_agent="data_analyst"
            )

            # Simulate data analyst response
            self.conversation_logger.log_message(
                "data_analyst",
                "Last quarter: 45% increase in engagement, 23% conversion rate",
                MessageType.UPDATE,
                to_agent=self.role
            )

            # Make a proposal
            self.log_proposal(
                "Based on the data, I propose a video-first campaign targeting our top-performing segments"
            )

            # Simulate skeptic challenge
            self.conversation_logger.log_message(
                "marketing_skeptic",
                "Video production is expensive. Have we considered the ROI?",
                MessageType.CHALLENGE,
                to_agent=self.role
            )

            # Respond to challenge
            self.log_update(
                "Good point. Our analysis shows video content has 3x ROI despite higher costs",
                to_agent="marketing_skeptic",
                confidence=0.85
            )

            # Make decision
            self.log_decision(
                "Approved: Video-first campaign with $50K budget, targeting Q2 launch",
                rationale="Data supports strong ROI, aligns with audience preferences"
            )

            return {
                "decision": "approved",
                "strategy": "video-first",
                "budget": 50000,
                "timeline": "Q2"
            }

    def log_proposal(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a proposal message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.PROPOSAL,
            to_agent=to_agent,
            metadata=metadata
        )

    def log_challenge(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a challenge/skeptical message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.CHALLENGE,
            to_agent=to_agent,
            metadata=metadata
        )

    def log_decision(self, message: str, **metadata):
        """Log a decision message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.DECISION,
            metadata=metadata
        )

    def log_update(self, message: str, to_agent: Optional[str] = None, **metadata):
        """Log a general update message"""
        self.conversation_logger.log_message(
            agent_name=self.role,
            message=message,
            message_type=MessageType.UPDATE,
            to_agent=to_agent,
            metadata=metadata
        )


if __name__ == "__main__":
    # Example usage
    manager = MarketingManagerWithLogging()

    # Simulate a campaign analysis
    result = manager.analyze_campaign_request(
        "Create a summer campaign to increase brand awareness among 25-34 demographic"
    )

    print(f"\\nCampaign Decision: {result}")

    # Show conversation metrics
    print(f"\\nConversation Metrics:")
    print(manager.conversation_logger.get_metrics())

    # Show natural language log
    log_file = Path(f"logs/conversations/{manager.team_name}_natural.log")
    if log_file.exists():
        print(f"\\nConversation Log:")
        print(log_file.read_text())
'''

    return example_agent


if __name__ == "__main__":
    print("=" * 60)
    print("Conversation Logging Integration Guide")
    print("=" * 60)

    # Save templates
    templates = create_logging_integration_template()

    print("\n1. CREWAI AGENT LOGGING TEMPLATE")
    print("-" * 40)
    print(templates["crewai"])

    print("\n2. TEAM FACTORY MODIFICATIONS")
    print("-" * 40)
    print(add_logging_to_team_factory())

    # Save setup script
    setup_script = create_setup_logging_script()
    with open("setup_conversation_logging.py", "w") as f:
        f.write(setup_script)
    print("\n✅ Created: setup_conversation_logging.py")

    # Save example agent
    example_agent = create_example_logged_agent()
    with open("example_logged_agent.py", "w") as f:
        f.write(example_agent)
    print("✅ Created: example_logged_agent.py")

    print("\n3. NEXT STEPS")
    print("-" * 40)
    print("1. Run 'python setup_conversation_logging.py' to set up Supabase tables")
    print("2. Add logging template code to team_factory.py")
    print("3. Run 'python example_logged_agent.py' to see logging in action")
    print("4. Create Quality Auditor team to analyze conversation logs")

    print(
        "\n✨ Conversation logging will enable continuous improvement through analysis!"
    )
