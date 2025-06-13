"""
LLM-based team analyzer for intelligent team composition and prompt generation.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path FIRST
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

try:
    from elf_automations.shared.utils.llm_factory import LLMFactory
except ImportError:
    # If still failing, use a mock for now
    print("Warning: LLMFactory not available, using mock")
    class LLMFactory:
            @staticmethod
            def create_llm(**kwargs):
                class MockLLM:
                    def invoke(self, prompt):
                        # Return a proper executive team structure
                        if "executive" in prompt.lower() or "leadership" in prompt.lower():
                            content = '''
                            {
                                "team_composition_rationale": "Executive leadership team with C-suite roles",
                                "roles": [
                                    {
                                        "title": "Chief Executive Officer",
                                        "is_manager": true,
                                        "rationale": "Overall strategic leadership and vision",
                                        "responsibilities": ["Set company vision", "Strategic planning", "Board relations"],
                                        "required_skills": ["leadership", "strategy", "communication"],
                                        "decision_authorities": ["final_approval", "resource_allocation"],
                                        "tools_needed": ["project_management", "communication", "analytics"],
                                        "personality_trait": "visionary",
                                        "success_contribution": "Drives overall company success"
                                    },
                                    {
                                        "title": "Chief Technology Officer",
                                        "is_manager": false,
                                        "rationale": "Technical strategy and innovation",
                                        "responsibilities": ["Technical strategy", "System architecture", "Innovation"],
                                        "required_skills": ["technical_leadership", "architecture", "innovation"],
                                        "decision_authorities": ["technical_decisions", "tool_selection"],
                                        "tools_needed": ["code_analysis", "monitoring", "architecture_tools"],
                                        "personality_trait": "analytical",
                                        "success_contribution": "Ensures technical excellence"
                                    },
                                    {
                                        "title": "Chief Marketing Officer",
                                        "is_manager": false,
                                        "rationale": "Brand and market growth",
                                        "responsibilities": ["Brand strategy", "Marketing campaigns", "Customer acquisition"],
                                        "required_skills": ["marketing", "creativity", "analytics"],
                                        "decision_authorities": ["marketing_budget", "brand_decisions"],
                                        "tools_needed": ["content_creation", "analytics", "communication"],
                                        "personality_trait": "creative",
                                        "success_contribution": "Drives market growth"
                                    },
                                    {
                                        "title": "Chief Operating Officer",
                                        "is_manager": false,
                                        "rationale": "Operational excellence",
                                        "responsibilities": ["Operations management", "Process optimization", "Team coordination"],
                                        "required_skills": ["operations", "process_management", "leadership"],
                                        "decision_authorities": ["operational_decisions", "process_changes"],
                                        "tools_needed": ["project_management", "monitoring", "analytics"],
                                        "personality_trait": "pragmatic",
                                        "success_contribution": "Ensures smooth operations"
                                    },
                                    {
                                        "title": "Chief Financial Officer",
                                        "is_manager": false,
                                        "rationale": "Financial health and compliance",
                                        "responsibilities": ["Financial planning", "Budget management", "Compliance"],
                                        "required_skills": ["finance", "analytics", "compliance"],
                                        "decision_authorities": ["budget_approval", "financial_decisions"],
                                        "tools_needed": ["financial", "analytics", "reporting"],
                                        "personality_trait": "detail_oriented",
                                        "success_contribution": "Maintains financial health"
                                    }
                                ],
                                "team_dynamics": "Collaborative C-suite with clear domains",
                                "risk_factors": ["Siloed thinking", "Communication gaps"],
                                "optimization_suggestions": ["Regular strategy sessions", "Cross-functional initiatives"]
                            }
                            '''
                        else:
                            # Generic team
                            content = '''
                            {
                                "team_composition_rationale": "Balanced team structure",
                                "roles": [
                                    {
                                        "title": "Team Lead",
                                        "is_manager": true,
                                        "personality_trait": "collaborative",
                                        "responsibilities": ["Team coordination", "Task assignment", "Delivery"],
                                        "required_skills": ["leadership", "communication", "planning"],
                                        "decision_authorities": ["task_assignment", "priority_setting"],
                                        "tools_needed": ["project_management", "communication"]
                                    },
                                    {
                                        "title": "Senior Specialist",
                                        "is_manager": false,
                                        "personality_trait": "analytical",
                                        "responsibilities": ["Technical work", "Mentoring", "Quality"],
                                        "required_skills": ["technical", "problem_solving", "mentoring"],
                                        "decision_authorities": ["technical_decisions"],
                                        "tools_needed": ["analytics", "monitoring"]
                                    },
                                    {
                                        "title": "Specialist",
                                        "is_manager": false,
                                        "personality_trait": "creative",
                                        "responsibilities": ["Implementation", "Innovation", "Support"],
                                        "required_skills": ["technical", "creativity", "collaboration"],
                                        "decision_authorities": ["implementation_decisions"],
                                        "tools_needed": ["development", "communication"]
                                    }
                                ]
                            }
                            '''
                        return type('Response', (), {'content': content})()
                return MockLLM()

from ..models import TeamSpecification, TeamMember, TeamCharter


@dataclass
class RoleDefinition:
    """Detailed role definition generated by LLM."""
    title: str
    responsibilities: List[str]
    required_skills: List[str]
    decision_authorities: List[str]
    tools_needed: List[str]
    interaction_style: str
    success_criteria: List[str]


class LLMTeamAnalyzer:
    """Uses LLM to analyze team requirements and generate optimal configurations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_team_requirements(
        self,
        charter: TeamCharter,
        description: str,
        framework: str,
        llm_provider: str,
        llm_model: str
    ) -> Dict[str, Any]:
        """
        Analyze team requirements using LLM to generate optimal team composition.
        
        Returns:
            Dict containing team composition, roles, and configurations
        """
        # Create LLM instance
        llm = LLMFactory.create_llm(
            preferred_provider=llm_provider.lower(),
            preferred_model=llm_model,
            temperature=0.7,
            team_name="team-factory"
        )
        
        # Create analysis prompt
        # Check if this is an AI-suggested composition (description starts with "Create a team to achieve:")
        is_ai_suggestion = description.startswith("Create a team to achieve:")
        
        if is_ai_suggestion:
            prompt_intro = """You are an expert in designing AI agent teams. Based on the charter below, 
design an optimal team composition that will achieve the stated objectives and success metrics.
Focus on creating a balanced team with complementary skills and clear role definitions."""
        else:
            prompt_intro = """You are an expert in designing AI agent teams. Based on the following charter and requirements, 
design an optimal team composition."""
        
        prompt = f"""
{prompt_intro}

TEAM CHARTER:
{charter.to_prompt_context()}

TEAM DESCRIPTION:
{description}

FRAMEWORK: {framework}

Please provide a detailed team composition with the following for each role:
1. Role title and why it's needed
2. Key responsibilities (3-5)
3. Required skills/expertise
4. Decision-making authorities
5. Tools/capabilities needed
6. Personality trait (from: skeptic, optimist, detail_oriented, innovator, pragmatist, collaborator, analytical)
7. How this role contributes to the team's objectives

Consider:
- Optimal team size is 3-7 members (5 is ideal)
- One member should be the manager/coordinator
- Teams of 5+ should have a skeptic for quality assurance
- Each role should directly support the charter's objectives
- Multi-team project coordination needs if applicable
- Balance different personality types for effective collaboration
- Ensure all success metrics have at least one role responsible for them
- Include both strategic and execution-focused roles

Provide your response as a JSON object with this structure:
{{
    "team_composition_rationale": "Why this specific team composition",
    "roles": [
        {{
            "title": "Role Title",
            "is_manager": true/false,
            "rationale": "Why this role is essential",
            "responsibilities": ["resp1", "resp2", "resp3"],
            "required_skills": ["skill1", "skill2"],
            "decision_authorities": ["authority1", "authority2"],
            "tools_needed": ["tool1", "tool2"],
            "personality_trait": "trait_name",
            "success_contribution": "How this role helps achieve objectives"
        }}
    ],
    "team_dynamics": "How these roles will work together",
    "risk_factors": ["potential challenge 1", "potential challenge 2"],
    "optimization_suggestions": ["suggestion 1", "suggestion 2"]
}}
"""
        
        try:
            response = llm.invoke(prompt)
            
            # Parse the response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                self.logger.info(f"Successfully analyzed team requirements: {len(result.get('roles', []))} roles identified")
                return result
            else:
                self.logger.error("Failed to extract JSON from LLM response")
                return self._get_fallback_composition(charter, description, framework)
                
        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {str(e)}")
            return self._get_fallback_composition(charter, description, framework)
    
    def generate_optimized_prompt(
        self,
        role: Dict[str, Any],
        charter: TeamCharter,
        team_context: str,
        framework: str,
        llm_provider: str,
        llm_model: str
    ) -> str:
        """
        Generate an optimized system prompt for a specific agent role.
        """
        # Create LLM instance
        llm = LLMFactory.create_llm(
            preferred_provider=llm_provider.lower(),
            preferred_model=llm_model,
            temperature=0.7,
            team_name="team-factory"
        )
        
        # Add project management context for managers
        pm_context = ""
        if role.get('is_manager') and charter.participates_in_multi_team_projects:
            pm_context = charter.to_manager_addendum()
        
        prompt = f"""
You are an expert in crafting effective AI agent prompts. Create an optimal system prompt for this agent:

ROLE: {role.get('title')}
RESPONSIBILITIES: {json.dumps(role.get('responsibilities', []))}
PERSONALITY: {role.get('personality_trait', 'collaborative')}

TEAM CHARTER:
{charter.to_prompt_context()}

TEAM CONTEXT:
{team_context}

{pm_context}

Create a system prompt that:
1. Clearly defines the agent's role and expertise
2. Incorporates their personality trait naturally
3. Establishes their responsibilities and boundaries
4. Defines how they interact with other team members
5. Aligns their work with the team's objectives and success metrics
6. Includes specific decision-making guidelines
7. For managers: includes project management responsibilities if applicable

The prompt should be:
- Clear and actionable
- Personality-appropriate (e.g., skeptics challenge constructively)
- Focused on achieving the team's objectives
- Specific about interaction patterns

Provide the complete system prompt as a single cohesive paragraph that the agent will use as their core identity.
"""
        
        try:
            response = llm.invoke(prompt)
            
            if hasattr(response, 'content'):
                optimized_prompt = response.content.strip()
            else:
                optimized_prompt = str(response).strip()
            
            self.logger.info(f"Generated optimized prompt for {role.get('title')}")
            return optimized_prompt
            
        except Exception as e:
            self.logger.error(f"Error generating optimized prompt: {str(e)}")
            return self._get_fallback_prompt(role, charter, pm_context)
    
    def _get_fallback_composition(self, charter: TeamCharter, description: str, framework: str) -> Dict[str, Any]:
        """
        Fallback team composition if LLM analysis fails.
        """
        self.logger.warning("Using fallback team composition")
        
        # Determine team type from description/department
        if "executive" in description.lower() or "leadership" in description.lower():
            return {
                "team_composition_rationale": "Executive team with C-suite roles",
                "roles": [
                    {
                        "title": "Chief Executive Officer",
                        "is_manager": True,
                        "personality_trait": "visionary",
                        "responsibilities": ["Set strategic direction", "Make final decisions", "Coordinate executives"],
                        "required_skills": ["leadership", "strategy", "communication"],
                        "decision_authorities": ["final_approval", "resource_allocation"],
                        "tools_needed": ["project_management", "communication", "analytics"]
                    },
                    {
                        "title": "Chief Technology Officer",
                        "is_manager": False,
                        "personality_trait": "analytical",
                        "responsibilities": ["Technical strategy", "System architecture", "Technology decisions"],
                        "required_skills": ["technical_leadership", "architecture", "innovation"],
                        "decision_authorities": ["technical_decisions", "tool_selection"],
                        "tools_needed": ["code_analysis", "architecture_tools", "monitoring"]
                    },
                    # Add more roles as needed
                ]
            }
        else:
            # Generic team
            return {
                "team_composition_rationale": "Generic balanced team",
                "roles": [
                    {
                        "title": "Team Lead",
                        "is_manager": True,
                        "personality_trait": "collaborative",
                        "responsibilities": ["Coordinate team", "Assign tasks", "Ensure delivery"],
                        "required_skills": ["leadership", "communication", "planning"],
                        "decision_authorities": ["task_assignment", "priority_setting"],
                        "tools_needed": ["project_management", "communication"]
                    }
                ]
            }
    
    def _get_fallback_prompt(self, role: Dict[str, Any], charter: TeamCharter, pm_context: str) -> str:
        """
        Generate a fallback prompt if LLM generation fails.
        """
        personality = role.get('personality_trait', 'collaborative')
        title = role.get('title', 'Team Member')
        
        base_prompt = f"""You are a {title} with a {personality} approach to your work. 
Your mission is to support the team in achieving: {charter.mission_statement}

Key responsibilities:
{chr(10).join(f"- {r}" for r in role.get('responsibilities', []))}

You work collaboratively with your team to achieve the objectives:
{chr(10).join(f"- {obj}" for obj in charter.primary_objectives[:3])}

{pm_context}"""
        
        return base_prompt