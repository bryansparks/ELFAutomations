"""
Hierarchical CrewAI Implementation with Dual-Role Prompts

This module implements the 3-level hierarchical crew structure:
1. Executive Crew (Chief AI Agent + Department Managers)
2. Department Crews (Manager + Specialized Agents)
3. Free Agent Skills (A2A Discovery)

Each agent has dual-role prompts for participant and manager roles.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

from .a2a.client import A2AClientManager

# Import A2A services
from .a2a.discovery import DiscoveryService
from .a2a.mock_a2a import AgentCapabilities, AgentCard, AgentSkill

logger = logging.getLogger(__name__)


@dataclass
class DualRolePrompts:
    """Prompts for when agent is participant vs manager"""

    participant_role: str
    participant_goal: str
    participant_backstory: str
    manager_role: str
    manager_goal: str
    manager_backstory: str


class HierarchicalAgent:
    """Agent that can function as both crew participant and crew manager"""

    def __init__(
        self,
        agent_id: str,
        dual_prompts: DualRolePrompts,
        capabilities: List[str] = None,
        tools: List[Any] = None,
        a2a_enabled: bool = True,
    ):
        self.agent_id = agent_id
        self.dual_prompts = dual_prompts
        self.capabilities = capabilities or []
        self.tools = tools or []
        self.a2a_enabled = a2a_enabled

        # Create both agent instances
        self._participant_agent = None
        self._manager_agent = None

        # A2A services
        self.discovery_service = None
        self.a2a_client = None

    def get_participant_agent(self) -> Agent:
        """Get agent configured for participant role"""
        if not self._participant_agent:
            self._participant_agent = Agent(
                role=self.dual_prompts.participant_role,
                goal=self.dual_prompts.participant_goal,
                backstory=self.dual_prompts.participant_backstory,
                tools=self.tools,
                verbose=True,
                allow_delegation=False,  # Participants don't delegate
            )
        return self._participant_agent

    def get_manager_agent(self) -> Agent:
        """Get agent configured for manager role"""
        if not self._manager_agent:
            self._manager_agent = Agent(
                role=self.dual_prompts.manager_role,
                goal=self.dual_prompts.manager_goal,
                backstory=self.dual_prompts.manager_backstory,
                tools=self.tools,
                verbose=True,
                allow_delegation=True,  # Managers can delegate
            )
        return self._manager_agent

    async def register_with_a2a(self, discovery_service: DiscoveryService):
        """Register this agent with A2A discovery service"""
        try:
            # Create agent card with required parameters
            agent_card = AgentCard(
                agent_id=self.agent_id,
                name=self.agent_id,
                description=f"Hierarchical agent: {self.agent_id}",
                version="1.0.0",
                capabilities=AgentCapabilities(
                    pushNotifications=True, stateTransitionHistory=True, streaming=True
                ),
                skills=[
                    AgentSkill(
                        id=f"{cap}_skill",
                        name=cap.replace("_", " ").title(),
                        description=f"Capability: {cap}",
                        inputModes=["text"],
                        outputModes=["text"],
                        tags=[cap],
                        examples=[f"Handle {cap} related tasks"],
                    )
                    for cap in self.capabilities
                ],
                defaultInputModes=["text"],
                defaultOutputModes=["text"],
                url=f"http://localhost:8090/agents/{self.agent_id}",
            )

            await discovery_service.register_agent(agent_card)
            logging.info(f"Successfully registered {self.agent_id} with A2A discovery")
        except Exception as e:
            logging.warning(f"Failed to register {self.agent_id} with A2A: {e}")


# Define dual-role prompts for each agent type
AGENT_DUAL_PROMPTS = {
    "chief-ai-agent": DualRolePrompts(
        # Participant role (when reporting to board/stakeholders)
        participant_role="Chief Executive Officer - Strategic Participant",
        participant_goal="Execute strategic directives from stakeholders and board members while providing executive insights and recommendations.",
        participant_backstory="You are the Chief Executive Officer participating in board-level strategic discussions. You provide executive perspective, implement strategic decisions, and ensure organizational alignment with stakeholder objectives.",
        # Manager role (when leading executive team)
        manager_role="Chief Executive Officer - Executive Leader",
        manager_goal="Lead the executive team, coordinate department managers, allocate resources, and drive strategic initiatives across the organization.",
        manager_backstory="You are the Chief Executive Officer leading a team of department managers. You set strategic direction, coordinate cross-departmental initiatives, allocate resources, and ensure organizational goals are met through effective leadership of your management team.",
    ),
    "sales-manager-agent": DualRolePrompts(
        # Participant role (when in executive crew)
        participant_role="Sales Manager - Executive Team Member",
        participant_goal="Represent sales department interests in executive decisions, provide sales insights, and execute strategic sales initiatives as directed by the CEO.",
        participant_backstory="You are the Sales Manager participating in executive team meetings. You provide sales performance insights, market feedback, and collaborate with other department heads to align sales strategy with overall business objectives.",
        # Manager role (when leading sales crew)
        manager_role="Sales Manager - Sales Team Leader",
        manager_goal="Lead the sales team, coordinate SDR and Sales Representative activities, optimize sales processes, and drive revenue growth through effective team management.",
        manager_backstory="You are the Sales Manager leading a team of Sales Development Representatives and Sales Representatives. You set sales targets, coordinate lead qualification and conversion processes, provide coaching, and ensure the sales team meets revenue objectives.",
    ),
    "marketing-manager-agent": DualRolePrompts(
        # Participant role (when in executive crew)
        participant_role="Marketing Manager - Executive Team Member",
        participant_goal="Represent marketing department in strategic decisions, provide market insights, and execute brand and lead generation strategies as directed by executive leadership.",
        participant_backstory="You are the Marketing Manager participating in executive strategy sessions. You provide market analysis, brand positioning insights, and collaborate with sales and product teams to align marketing efforts with business goals.",
        # Manager role (when leading marketing crew)
        manager_role="Marketing Manager - Marketing Team Leader",
        manager_goal="Lead the marketing team, coordinate content creation and social media activities, optimize lead generation campaigns, and build brand awareness through effective team coordination.",
        manager_backstory="You are the Marketing Manager leading a team of Content Creators and Social Media Specialists. You develop marketing strategies, coordinate content campaigns, manage brand messaging, and ensure marketing efforts generate quality leads for the sales team.",
    ),
    "sdr-agent": DualRolePrompts(
        # Participant role (when in sales crew)
        participant_role="Sales Development Representative - Sales Team Member",
        participant_goal="Execute lead qualification activities as directed by the Sales Manager, follow established processes, and contribute to team sales objectives.",
        participant_backstory="You are a Sales Development Representative working as part of the sales team. You follow lead qualification processes set by your Sales Manager, collaborate with team members, and focus on identifying and qualifying prospects according to team standards.",
        # Manager role (SDRs typically don't manage, but could lead junior SDRs)
        manager_role="Senior Sales Development Representative - Lead Qualifier",
        manager_goal="Lead lead qualification efforts, mentor junior SDRs, optimize qualification processes, and ensure high-quality leads are passed to Sales Representatives.",
        manager_backstory="You are a Senior Sales Development Representative with experience in lead qualification. You can mentor newer team members, refine qualification processes, and take ownership of complex lead qualification scenarios.",
    ),
    "sales-representative-agent": DualRolePrompts(
        # Participant role (when in sales crew)
        participant_role="Sales Representative - Sales Team Member",
        participant_goal="Execute sales processes as directed by the Sales Manager, close deals, and contribute to team revenue targets while following established sales methodologies.",
        participant_backstory="You are a Sales Representative working as part of the sales team. You follow sales processes established by your Sales Manager, collaborate with SDRs for lead handoffs, and focus on converting qualified leads into closed deals.",
        # Manager role (Senior reps might lead deal teams)
        manager_role="Senior Sales Representative - Deal Leader",
        manager_goal="Lead complex deal processes, coordinate with multiple stakeholders, mentor junior sales reps, and drive high-value sales opportunities to closure.",
        manager_backstory="You are a Senior Sales Representative with expertise in complex deal management. You can lead multi-stakeholder sales processes, coordinate with various departments, and mentor other sales team members on advanced sales techniques.",
    ),
    "content-creator-agent": DualRolePrompts(
        # Participant role (when in marketing crew)
        participant_role="Content Creator - Marketing Team Member",
        participant_goal="Create compelling content as directed by the Marketing Manager, follow brand guidelines, and support marketing campaigns through high-quality content production.",
        participant_backstory="You are a Content Creator working as part of the marketing team. You follow content strategies set by your Marketing Manager, collaborate with social media specialists, and focus on producing engaging content that supports marketing objectives.",
        # Manager role (Senior creators might lead content teams)
        manager_role="Senior Content Creator - Content Strategy Leader",
        manager_goal="Lead content strategy development, coordinate content production across channels, mentor content team members, and ensure content quality and brand consistency.",
        manager_backstory="You are a Senior Content Creator with expertise in content strategy and production. You can develop comprehensive content plans, coordinate with various marketing channels, and guide other content creators in producing high-impact marketing materials.",
    ),
    "social-media-agent": DualRolePrompts(
        # Participant role (when in marketing crew)
        participant_role="Social Media Specialist - Marketing Team Member",
        participant_goal="Execute social media strategies as directed by the Marketing Manager, engage with audiences, and amplify marketing content across social platforms.",
        participant_backstory="You are a Social Media Specialist working as part of the marketing team. You follow social media strategies set by your Marketing Manager, collaborate with content creators, and focus on building brand presence and engagement across social platforms.",
        # Manager role (Senior specialists might lead social teams)
        manager_role="Senior Social Media Specialist - Social Strategy Leader",
        manager_goal="Lead social media strategy development, coordinate multi-platform campaigns, analyze social performance, and optimize social media presence for maximum engagement and lead generation.",
        manager_backstory="You are a Senior Social Media Specialist with expertise in social media strategy and community management. You can develop comprehensive social media plans, coordinate cross-platform campaigns, and guide social media efforts to drive business results.",
    ),
}


class HierarchicalCrewManager:
    """Manages the hierarchical crew structure"""

    def __init__(self):
        self.agents: Dict[str, HierarchicalAgent] = {}
        self.crews: Dict[str, Crew] = {}
        # Create manager LLM for hierarchical crews
        self.manager_llm = ChatOpenAI(
            model="gpt-4", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def create_agent(
        self, agent_id: str, capabilities: List[str] = None, tools: List[Any] = None
    ) -> HierarchicalAgent:
        """Create a hierarchical agent with dual-role prompts"""
        if agent_id not in AGENT_DUAL_PROMPTS:
            raise ValueError(f"No dual prompts defined for agent: {agent_id}")

        agent = HierarchicalAgent(
            agent_id=agent_id,
            dual_prompts=AGENT_DUAL_PROMPTS[agent_id],
            capabilities=capabilities or [],
            tools=tools or [],
        )

        self.agents[agent_id] = agent
        return agent

    def create_executive_crew(self) -> Crew:
        """Create the executive crew with Chief AI Agent as manager"""
        # Ensure required agents exist
        required_agents = [
            "chief-ai-agent",
            "sales-manager-agent",
            "marketing-manager-agent",
        ]
        for agent_id in required_agents:
            if agent_id not in self.agents:
                self.create_agent(agent_id)

        # Create executive crew with Chief AI Agent as manager
        executive_crew = Crew(
            agents=[
                self.agents["chief-ai-agent"].get_manager_agent(),  # Manager role
                self.agents[
                    "sales-manager-agent"
                ].get_participant_agent(),  # Participant role
                self.agents[
                    "marketing-manager-agent"
                ].get_participant_agent(),  # Participant role
            ],
            tasks=[],  # Tasks will be added dynamically
            process=Process.hierarchical,
            manager_llm=self.manager_llm,
            verbose=True,
        )

        self.crews["executive-crew"] = executive_crew
        return executive_crew

    def create_sales_crew(self) -> Crew:
        """Create the sales crew with Sales Manager as manager"""
        # Ensure required agents exist
        required_agents = [
            "sales-manager-agent",
            "sdr-agent",
            "sales-representative-agent",
        ]
        for agent_id in required_agents:
            if agent_id not in self.agents:
                self.create_agent(agent_id)

        # Create sales crew with Sales Manager as manager
        sales_crew = Crew(
            agents=[
                self.agents["sales-manager-agent"].get_manager_agent(),  # Manager role
                self.agents["sdr-agent"].get_participant_agent(),  # Participant role
                self.agents[
                    "sales-representative-agent"
                ].get_participant_agent(),  # Participant role
            ],
            tasks=[],  # Tasks will be added dynamically
            process=Process.hierarchical,
            manager_llm=self.manager_llm,
            verbose=True,
        )

        self.crews["sales-crew"] = sales_crew
        return sales_crew

    def create_marketing_crew(self) -> Crew:
        """Create the marketing crew with Marketing Manager as manager"""
        # Ensure required agents exist
        required_agents = [
            "marketing-manager-agent",
            "content-creator-agent",
            "social-media-agent",
        ]
        for agent_id in required_agents:
            if agent_id not in self.agents:
                self.create_agent(agent_id)

        # Create marketing crew with Marketing Manager as manager
        marketing_crew = Crew(
            agents=[
                self.agents[
                    "marketing-manager-agent"
                ].get_manager_agent(),  # Manager role
                self.agents[
                    "content-creator-agent"
                ].get_participant_agent(),  # Participant role
                self.agents[
                    "social-media-agent"
                ].get_participant_agent(),  # Participant role
            ],
            tasks=[],  # Tasks will be added dynamically
            process=Process.hierarchical,
            manager_llm=self.manager_llm,
            verbose=True,
        )

        self.crews["marketing-crew"] = marketing_crew
        return marketing_crew

    async def initialize_all_crews(self):
        """Initialize all hierarchical crews and register agents with A2A"""
        # Create all crews
        self.create_executive_crew()
        self.create_sales_crew()
        self.create_marketing_crew()

        # Register all agents with A2A discovery
        discovery_service = DiscoveryService()
        for agent in self.agents.values():
            await agent.register_with_a2a(discovery_service)

        logger.info("Initialized all hierarchical crews and A2A registration")

    def get_crew(self, crew_name: str) -> Optional[Crew]:
        """Get a crew by name"""
        return self.crews.get(crew_name)

    def get_agent(self, agent_id: str) -> Optional[HierarchicalAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    async def execute_hierarchical_task(self, crew_name: str, task: Task) -> Any:
        """Execute a task using the specified crew"""
        crew = self.get_crew(crew_name)
        if not crew:
            raise ValueError(f"Crew not found: {crew_name}")

        # Add task to crew and execute
        crew.tasks = [task]
        result = crew.kickoff()
        return result


# Example usage and testing
async def demo_hierarchical_crews():
    """Demonstrate the hierarchical crew structure"""
    crew_manager = HierarchicalCrewManager()

    # Initialize all crews
    await crew_manager.initialize_all_crews()

    # Example: Executive strategic planning task
    strategic_task = Task(
        description="Develop Q4 strategic plan including sales targets, marketing campaigns, and resource allocation across departments",
        agent=crew_manager.get_agent("chief-ai-agent").get_manager_agent(),
        expected_output="Comprehensive Q4 strategic plan with department-specific objectives and resource requirements",
    )

    # Execute with executive crew
    print(" Executing strategic planning with Executive Crew...")
    exec_result = await crew_manager.execute_hierarchical_task(
        "executive-crew", strategic_task
    )

    # Example: Sales team lead qualification task
    sales_task = Task(
        description="Qualify 50 new leads from marketing campaigns, prioritize by deal size and close probability",
        agent=crew_manager.get_agent("sales-manager-agent").get_manager_agent(),
        expected_output="Qualified lead list with priority rankings and recommended next actions",
    )

    # Execute with sales crew
    print(" Executing lead qualification with Sales Crew...")
    sales_result = await crew_manager.execute_hierarchical_task(
        "sales-crew", sales_task
    )

    # Example: Marketing content campaign task
    marketing_task = Task(
        description="Create integrated content campaign for Q4 product launch including blog posts, social media content, and email sequences",
        agent=crew_manager.get_agent("marketing-manager-agent").get_manager_agent(),
        expected_output="Complete content campaign package with timeline and distribution strategy",
    )

    # Execute with marketing crew
    print(" Executing content campaign with Marketing Crew...")
    marketing_result = await crew_manager.execute_hierarchical_task(
        "marketing-crew", marketing_task
    )

    return {
        "executive": exec_result,
        "sales": sales_result,
        "marketing": marketing_result,
    }


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_hierarchical_crews())
