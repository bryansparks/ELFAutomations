"""
Core TeamFactory class - orchestrates team creation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..generators.agents.crewai_v2 import CrewAIAgentGenerator
from ..generators.agents.langgraph import LangGraphAgentGenerator
from ..generators.config.a2a import A2AConfigGenerator
from ..generators.config.llm_config import LLMConfigGenerator
from ..generators.config.team_config import TeamConfigGenerator
from ..generators.documentation.readme import ReadmeGenerator
from ..generators.infrastructure.deployment import DeploymentScriptGenerator
from ..generators.infrastructure.docker import DockerfileGenerator
from ..generators.infrastructure.fastapi_server import FastAPIServerGenerator
from ..generators.infrastructure.kubernetes import KubernetesGenerator
from ..generators.orchestrators.crew import CrewAIOrchestrator
from ..generators.orchestrators.workflow import LangGraphWorkflow
from ..generators.llm_analyzer import LLMTeamAnalyzer
from ..generators.tools.agent_tools import AgentToolGenerator
from ..generators.evolution.improvement_loop import ImprovementLoopGenerator
from ..integrations.executive_patch import ExecutivePatchGenerator
from ..integrations.memory import MemorySystemIntegration
from ..integrations.registry import RegistryIntegration
from ..models import SubTeamRecommendation, TeamMember, TeamSpecification
from ..ui.console import TeamFactoryConsole
from ..utils.constants import (
    DEPARTMENT_EXECUTIVE_MAPPING,
    MAX_TEAM_SIZE,
    MIN_TEAM_SIZE,
    PERSONALITY_TRAITS,
    SKEPTIC_THRESHOLD,
)
from ..utils.validators import validate_team_spec


class TeamFactory:
    """Main factory class for creating AI teams."""

    def __init__(self):
        """Initialize the team factory."""
        self.console = Console()
        self.ui = TeamFactoryConsole()
        self.logger = logging.getLogger(__name__)
        self.generated_teams = []
        
        # Initialize generators
        self.agent_generators = {
            "CrewAI": CrewAIAgentGenerator(),
            "LangGraph": LangGraphAgentGenerator(),
        }
        
        self.orchestrator_generators = {
            "CrewAI": CrewAIOrchestrator(),
            "LangGraph": LangGraphWorkflow(),
        }
        
        self.infrastructure_generators = {
            "docker": DockerfileGenerator(),
            "kubernetes": KubernetesGenerator(),
            "deployment": DeploymentScriptGenerator(),
            "server": FastAPIServerGenerator(),
        }
        
        self.config_generators = {
            "team": TeamConfigGenerator(),
            "a2a": A2AConfigGenerator(),
            "llm": LLMConfigGenerator(),
        }
        
        self.documentation_generator = ReadmeGenerator()
        
        # Initialize generators
        self.tool_generator = AgentToolGenerator()
        self.evolution_generator = ImprovementLoopGenerator()
        
        # Initialize integrations
        self.registry = RegistryIntegration()
        self.memory = MemorySystemIntegration()
        self.executive_patch = ExecutivePatchGenerator()
        
        # Initialize LLM analyzer
        self.llm_analyzer = LLMTeamAnalyzer()

    def analyze_request(
        self, 
        spec: TeamSpecification
    ) -> TeamSpecification:
        """
        Analyze team requirements using LLM to generate optimal composition.
        
        Args:
            spec: Initial team specification with charter and description
            
        Returns:
            Enhanced TeamSpecification with LLM-generated team composition
        """
        if not spec.charter:
            self.logger.warning("No charter provided, using basic analysis")
            return spec
            
        self.ui.show_progress("Analyzing team requirements with AI...")
        
        # Use LLM to analyze and generate team composition
        analysis = self.llm_analyzer.analyze_team_requirements(
            charter=spec.charter,
            description=spec.natural_language_description,
            framework=spec.framework,
            llm_provider=spec.llm_provider,
            llm_model=spec.llm_model
        )
        
        # Convert analysis to team members
        members = []
        for idx, role in enumerate(analysis.get('roles', [])):
            # Generate optimized prompt for this role
            self.ui.show_progress(f"Optimizing prompt for {role.get('title')}...")
            
            system_prompt = self.llm_analyzer.generate_optimized_prompt(
                role=role,
                charter=spec.charter,
                team_context=analysis.get('team_dynamics', ''),
                framework=spec.framework,
                llm_provider=spec.llm_provider,
                llm_model=spec.llm_model
            )
            
            member = TeamMember(
                name=role.get('title', '').lower().replace(' ', '_'),
                role=role.get('title', f'Team Member {idx+1}'),
                system_prompt=system_prompt,
                backstory=role.get('rationale', ''),
                personality=role.get('personality_trait', 'collaborative'),
                responsibilities=role.get('responsibilities', []),
                skills=role.get('required_skills', []),
                tools=role.get('tools_needed', []),
                is_manager=role.get('is_manager', False),
                collaboration_style=role.get('interaction_style', 'cooperative'),
                decision_authority=role.get('decision_authorities', [])
            )
            members.append(member)
        
        # Update specification with LLM-generated composition
        spec.members = members
        spec.created_by_llm = True
        
        # Add team skills based on member skills
        all_skills = set()
        for member in members:
            all_skills.update(member.skills)
        spec.skills = list(all_skills)
        
        # Add any optimization suggestions as warnings/notes
        if 'optimization_suggestions' in analysis:
            self.logger.info(f"Optimization suggestions: {analysis['optimization_suggestions']}")
        
        return spec

    def create_team(self, spec: TeamSpecification) -> Dict[str, Any]:
        """
        Create a team based on the specification.

        This is the main entry point for team creation.
        """
        results = {
            "success": True,
            "errors": [],
            "warnings": [],
            "generated_files": [],
            "team_path": str((Path("teams") / spec.name).absolute()),
        }
        
        try:
            # Validate specification
            validation_errors = validate_team_spec(spec)
            if validation_errors:
                results["errors"] = validation_errors
                results["success"] = False
                return results
            
            # Create team directory in teams/ folder
            teams_base = Path("teams")
            teams_base.mkdir(exist_ok=True)  # Create teams/ if it doesn't exist
            
            team_dir = teams_base / spec.name
            if team_dir.exists():
                results["errors"].append(f"Team directory 'teams/{spec.name}' already exists")
                results["success"] = False
                return results
            
            team_dir.mkdir(parents=True)
            self.logger.info(f"Created team directory: {team_dir}")
            
            # Generate agents
            self.ui.show_progress("Generating agents...")
            agent_gen = self.agent_generators[spec.framework]
            agent_results = agent_gen.generate(spec)
            results["generated_files"].extend(agent_results["generated_files"])
            if agent_results.get("errors"):
                results["errors"].extend(agent_results["errors"])
            
            # Generate orchestrator
            self.ui.show_progress("Creating orchestrator...")
            orch_gen = self.orchestrator_generators[spec.framework]
            orch_results = orch_gen.generate(spec)
            results["generated_files"].extend(orch_results["generated_files"])
            if orch_results.get("errors"):
                results["errors"].extend(orch_results["errors"])
            
            # Generate infrastructure
            self.ui.show_progress("Setting up infrastructure...")
            for name, generator in self.infrastructure_generators.items():
                infra_results = generator.generate(spec)
                results["generated_files"].extend(infra_results["generated_files"])
                if infra_results.get("errors"):
                    results["errors"].extend(infra_results["errors"])
            
            # Generate configurations
            self.ui.show_progress("Creating configurations...")
            config_dir = team_dir / "config"
            config_dir.mkdir(exist_ok=True)
            
            for name, generator in self.config_generators.items():
                config_results = generator.generate(spec)
                results["generated_files"].extend(config_results["generated_files"])
                if config_results.get("errors"):
                    results["errors"].extend(config_results["errors"])
            
            # Generate documentation
            self.ui.show_progress("Writing documentation...")
            doc_results = self.documentation_generator.generate(spec)
            results["generated_files"].extend(doc_results["generated_files"])
            if doc_results.get("errors"):
                results["errors"].extend(doc_results["errors"])
            
            # Create standard directories
            for subdir in ["tasks", "logs"]:
                (team_dir / subdir).mkdir(exist_ok=True)
                init_file = team_dir / subdir / "__init__.py"
                init_file.write_text("")
                results["generated_files"].append(str(init_file))
            
            # Generate role-specific tools
            self.ui.show_progress("Generating role-specific tools...")
            tool_results = self.tool_generator.generate_tools(spec)
            results["generated_files"].extend(tool_results["generated_files"])
            if tool_results.get("errors"):
                results["errors"].extend(tool_results["errors"])
            
            # Generate evolution/improvement loop if enabled
            if spec.enable_evolution:
                self.ui.show_progress("Setting up improvement loop...")
                evolution_results = self.evolution_generator.generate(spec)
                results["generated_files"].extend(evolution_results["generated_files"])
                if evolution_results.get("errors"):
                    results["errors"].extend(evolution_results["errors"])
            
            # Register with team registry
            self.ui.show_progress("Registering team...")
            try:
                registry_result = self.registry.register_team(spec)
                if registry_result.get("success"):
                    results["warnings"].append("Team registered in Supabase")
                else:
                    results["warnings"].append("Failed to register team in Supabase")
            except Exception as e:
                results["warnings"].append(f"Registry error: {str(e)}")
            
            # Set up memory system
            self.ui.show_progress("Configuring memory system...")
            try:
                memory_result = self.memory.setup_team_memory(spec)
                if memory_result.get("success"):
                    results["warnings"].append("Memory system configured")
                else:
                    results["warnings"].append("Failed to configure memory system")
            except Exception as e:
                results["warnings"].append(f"Memory setup error: {str(e)}")
            
            # Generate executive patch if reporting to executive
            if spec.reporting_to and spec.reporting_to.upper() in ["CEO", "CTO", "CMO", "COO", "CFO"]:
                self.ui.show_progress("Creating executive patch...")
                try:
                    patch_result = self.executive_patch.generate_patch(spec)
                    if patch_result.get("patch_file"):
                        results["generated_files"].append(patch_result["patch_file"])
                        results["warnings"].append(
                            f"Created executive patch: {patch_result['patch_file']}"
                        )
                except Exception as e:
                    results["warnings"].append(f"Executive patch error: {str(e)}")
            
            # Create summary
            self._create_summary_file(spec, results, team_dir)
            
            # Track generated team
            self.generated_teams.append(spec)
            
        except Exception as e:
            import traceback
            self.logger.error(f"Error creating team: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            results["errors"].append(f"Unexpected error: {str(e)}")
            results["success"] = False
        
        return results
    
    def _create_summary_file(
        self, spec: TeamSpecification, results: Dict[str, Any], team_dir: Path
    ) -> None:
        """Create a summary file with creation details."""
        summary = {
            "team_name": spec.name,
            "framework": spec.framework,
            "department": spec.department,
            "created_at": datetime.now().isoformat(),
            "llm_provider": spec.llm_provider,
            "llm_model": spec.llm_model,
            "members": [
                {
                    "role": m.role,
                    "personality": m.personality,
                    "is_manager": m.is_manager,
                }
                for m in spec.members
            ],
            "generated_files": results["generated_files"],
            "warnings": results["warnings"],
        }
        
        summary_file = team_dir / ".team_factory_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        results["generated_files"].append(str(summary_file))

    def validate_team_size(self, team_size: int) -> str:
        """Validate team size against constraints."""
        if team_size < MIN_TEAM_SIZE:
            return f"Team size ({team_size}) is below minimum ({MIN_TEAM_SIZE})"
        elif team_size > MAX_TEAM_SIZE:
            return f"Team size ({team_size}) exceeds maximum ({MAX_TEAM_SIZE})"
        else:
            return f"Team size ({team_size}) is within acceptable range"

    def should_add_skeptic(self, team_size: int) -> bool:
        """Determine if team should have a skeptic."""
        return team_size >= SKEPTIC_THRESHOLD

    def get_reporting_executive(self, department: str) -> str:
        """Get the executive a department reports to."""
        return DEPARTMENT_EXECUTIVE_MAPPING.get(department.lower(), "CEO")

    def get_personality_modifiers(self, personality: str) -> List[str]:
        """Get personality trait modifiers."""
        trait = PERSONALITY_TRAITS.get(personality, {})
        return trait.get("modifiers", [])
