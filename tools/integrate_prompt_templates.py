#!/usr/bin/env python3
"""
Integration script to add prompt template system to existing team_factory.py
This shows how to modify team_factory.py to use the new prompt system
"""

import os
import sys


def generate_integration_code():
    """Generate the code changes needed for team_factory.py"""

    integration_code = '''
# Add this import at the top of team_factory.py
from prompt_template_system import PromptTemplateSystem

# Add this to the __init__ method of TeamFactory class
self.prompt_system = PromptTemplateSystem()

# Replace the _generate_system_prompt method with this enhanced version
def _generate_system_prompt(self, team_member: TeamMember, team_name: str,
                          team_description: str, all_members: List[TeamMember]) -> str:
    """Generate enhanced contextual system prompt for an agent"""

    # First check if we have a predefined prompt (for backward compatibility)
    if team_member.system_prompt and not team_member.system_prompt.startswith("You are"):
        return team_member.system_prompt

    # Generate team context if not exists
    team_context_file = self.prompt_system.template_dir / f"{team_name}_context.yaml"
    if not team_context_file.exists():
        print(f"\\n🎯 Let's define the context for {team_name}")
        team_context = self.prompt_system.generate_team_context(
            team_name,
            team_description,
            parent_team=None  # Could be enhanced to track parent teams
        )
    else:
        import yaml
        with open(team_context_file, 'r') as f:
            team_context = yaml.safe_load(f)

    # Prepare member data
    members_data = [
        {"name": m.name, "role": m.role}
        for m in all_members
    ]

    # Generate custom details
    custom_details = {
        'tools': [tool.name for tool in team_member.tools] if hasattr(team_member, 'tools') else [],
        'specific_knowledge': getattr(team_member, 'expertise', '')
    }

    # Generate the enhanced prompt
    enhanced_prompt = self.prompt_system.generate_agent_prompt(
        agent_name=team_member.name,
        agent_role=team_member.role,
        team_context=team_context,
        team_members=members_data,
        custom_details=custom_details
    )

    return enhanced_prompt

# Add this method to allow post-generation prompt modification
def modify_agent_prompt(self, team_name: str, agent_name: str):
    """Modify an existing agent's prompt"""
    return self.prompt_system.modify_agent_prompt(team_name, agent_name)

# Modify the create_team method to use enhanced prompts
# In the section where agents are created, replace:
# system_prompt=member.system_prompt
# with:
# system_prompt=self._generate_system_prompt(member, team_name, description, team_members)
'''

    return integration_code


def create_example_usage():
    """Create an example script showing how to use the enhanced team factory"""

    example_code = '''#!/usr/bin/env python3
"""
Example usage of enhanced team factory with prompt templates
"""

from team_factory import TeamFactory

def create_team_with_rich_prompts():
    """Example of creating a team with enhanced contextual prompts"""

    factory = TeamFactory()

    print("\\n🚀 Enhanced Team Factory with Contextual Prompts\\n")

    # The factory will now guide you through creating rich context
    # for your team, resulting in much more effective agents

    # Create a team - the process now includes context gathering
    factory.create_team()

    print("\\n✅ Team created with enhanced contextual prompts!")

def modify_existing_agent():
    """Example of modifying an existing agent's prompt"""

    factory = TeamFactory()

    team_name = input("Enter team name: ")
    agent_name = input("Enter agent name: ")

    factory.modify_agent_prompt(team_name, agent_name)

if __name__ == "__main__":
    print("1. Create new team with rich prompts")
    print("2. Modify existing agent prompt")

    choice = input("\\nSelect option (1-2): ")

    if choice == "1":
        create_team_with_rich_prompts()
    elif choice == "2":
        modify_existing_agent()
'''

    return example_code


def create_templates_directory():
    """Create the templates directory structure"""

    templates_dir = "templates/prompts"
    os.makedirs(templates_dir, exist_ok=True)

    # Create a sample team template
    sample_template = """# Team Template: Engineering Team
# This template can be used as a starting point for technical teams

team_context:
  purpose: "Build and maintain robust, scalable systems that delight users"
  goals:
    - "Deliver features on time with high quality"
    - "Maintain 99.9% uptime for critical services"
    - "Foster a culture of continuous learning"
  constraints:
    - "Limited to 5 engineers initially"
    - "Must use existing tech stack"
    - "Security and compliance are non-negotiable"
  success_metrics:
    - "Code review turnaround < 24 hours"
    - "Test coverage > 80%"
    - "Customer-reported bugs < 5 per sprint"

agent_prompts:
  engineering_manager:
    additional_context: |
      You have 10 years of experience building distributed systems.
      You believe in servant leadership and removing blockers for your team.
      You're passionate about mentoring junior engineers.

  senior_engineer:
    additional_context: |
      You're an expert in system design and performance optimization.
      You enjoy tackling complex technical challenges.
      You actively contribute to open source projects.

  security_engineer:
    additional_context: |
      You think like an attacker to build better defenses.
      You stay current with the latest security threats and mitigations.
      You believe security should be built in, not bolted on.
"""

    with open(os.path.join(templates_dir, "engineering_team_template.yaml"), "w") as f:
        f.write(sample_template)

    print(f"✅ Created templates directory at {templates_dir}")
    print(f"✅ Added sample template: engineering_team_template.yaml")


if __name__ == "__main__":
    print("=" * 60)
    print("INTEGRATION GUIDE: Adding Prompt Templates to Team Factory")
    print("=" * 60)

    print("\\n1. INTEGRATION CODE")
    print("-" * 40)
    print(generate_integration_code())

    print("\\n2. EXAMPLE USAGE")
    print("-" * 40)

    # Save example usage file
    with open("use_enhanced_team_factory.py", "w") as f:
        f.write(create_example_usage())

    print("✅ Created: use_enhanced_team_factory.py")

    print("\\n3. CREATING TEMPLATE STRUCTURE")
    print("-" * 40)
    create_templates_directory()

    print("\\n4. NEXT STEPS")
    print("-" * 40)
    print("1. Add the import and methods from the integration code to team_factory.py")
    print(
        "2. Run 'python use_enhanced_team_factory.py' to create a team with rich prompts"
    )
    print("3. Customize templates in templates/prompts/ for your specific needs")
    print("4. Use modify_agent_prompt() to refine prompts based on performance")

    print(
        "\\n✨ The prompt template system will make your agents significantly more effective!"
    )
