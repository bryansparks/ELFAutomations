#!/usr/bin/env python3
"""
N8N Workflow Factory V3

AI-enhanced workflow generator with advanced agent support, RAG patterns, and safety controls.
Incorporates 2024-2025 best practices for AI workflow automation.
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import Client, create_client

from elf_automations.shared.n8n import N8NClient, WorkflowCategory, WorkflowTriggerType
from elf_automations.shared.n8n.agent_nodes import (
    AgentNodeBuilder,
    ChainNodeBuilder,
    MemoryNodeBuilder,
    OutputParserBuilder,
    VectorStoreNodeBuilder,
    create_multi_agent_workflow,
)
from elf_automations.shared.n8n.ai_patterns import (
    AIModelProvider,
    AINodeConfiguration,
    AIWorkflowPattern,
    AIWorkflowPatterns,
    detect_ai_pattern,
)
from elf_automations.shared.n8n.config import TeamConfiguration, WorkflowConfig
from elf_automations.shared.n8n.patterns import (
    InputSource,
    OutputChannel,
    StorageType,
    WorkflowPattern,
    detect_pattern,
    generate_pattern_nodes,
)
from elf_automations.shared.n8n.templates import (
    WorkflowTemplates,
    get_template,
    list_templates,
)
from elf_automations.shared.utils.llm_factory import LLMFactory

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class AIEnhancedWorkflowFactory:
    """Enhanced factory with AI agent support and intelligent generation"""

    def __init__(self, team_name: str = "default"):
        self.team_name = team_name
        self.config = WorkflowConfig()
        self.team_config = self.config.get_team_config(team_name)

        # Use Claude for better workflow understanding
        self.llm = LLMFactory.create_llm(
            preferred_provider="anthropic",
            preferred_model="claude-3-opus-20240229",
            temperature=0.1,
            enable_fallback=True,
        )

        # Initialize Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            raise ValueError("Supabase credentials not found")

        # Extended node type mapping including AI nodes
        self.node_types = {
            # Standard nodes
            "webhook": "n8n-nodes-base.webhook",
            "schedule": "n8n-nodes-base.scheduleTrigger",
            "http": "n8n-nodes-base.httpRequest",
            "database": "n8n-nodes-base.postgres",
            "supabase": "n8n-nodes-base.supabase",
            "transform": "n8n-nodes-base.code",
            "filter": "n8n-nodes-base.if",
            "switch": "n8n-nodes-base.switch",
            "merge": "n8n-nodes-base.merge",
            "slack": "n8n-nodes-base.slack",
            "email": "n8n-nodes-base.emailSend",
            # AI nodes
            "ai_agent": "@n8n/n8n-nodes-langchain.agent",
            "vector_store": "@n8n/n8n-nodes-langchain.vectorStore",
            "memory": "@n8n/n8n-nodes-langchain.memory",
            "chain": "@n8n/n8n-nodes-langchain.chain",
            "output_parser": "@n8n/n8n-nodes-langchain.outputParser",
            "embeddings": "@n8n/n8n-nodes-langchain.embeddings",
            "document_loader": "@n8n/n8n-nodes-langchain.documentLoader",
            "text_splitter": "@n8n/n8n-nodes-langchain.textSplitter",
        }

    async def analyze_ai_requirements(
        self, description: str
    ) -> Tuple[Optional[AIWorkflowPattern], Dict[str, Any]]:
        """Analyze description for AI-specific requirements"""

        # First try AI pattern detection
        ai_pattern, ai_config = detect_ai_pattern(description)

        if not ai_pattern:
            # Use LLM to analyze if AI is needed
            prompt = f"""Analyze this workflow description to determine if it requires AI capabilities:

Description: {description}

Determine:
1. Does this need AI agents? (yes/no)
2. What type of AI processing? (conversation, analysis, generation, etc.)
3. Does it need memory/context? (yes/no)
4. Does it need RAG/vector search? (yes/no)
5. What tools might be needed? (list specific tools)
6. Safety requirements? (content filtering, PII, rate limiting, etc.)

Return as JSON:
{{
    "needs_ai": true/false,
    "ai_type": "conversation/analysis/generation/orchestration",
    "needs_memory": true/false,
    "needs_rag": true/false,
    "suggested_tools": ["tool1", "tool2"],
    "safety_requirements": ["requirement1", "requirement2"],
    "suggested_pattern": "pattern_name or null"
}}"""

            response = self.llm.invoke(prompt)
            analysis = json.loads(response.content)

            if analysis.get("needs_ai"):
                # Create a custom AI pattern based on analysis
                ai_config = analysis
            else:
                return None, {}

        return ai_pattern, ai_config

    def generate_ai_workflow_nodes(
        self, pattern: AIWorkflowPattern, config: Dict[str, Any], name: str
    ) -> Dict[str, Any]:
        """Generate nodes for an AI workflow pattern"""

        nodes = []
        connections = {}
        node_positions = {"x": 250, "y": 300}

        def add_node(node: Dict[str, Any], x: int, y: int) -> str:
            """Add a node at the specified position"""
            node["position"] = [x, y]
            if "id" not in node:
                node["id"] = f"node_{len(nodes)}"
            nodes.append(node)
            return node["name"]

        # 1. Create trigger node
        trigger_node = self._create_trigger_node(
            pattern.inputs[0] if pattern.inputs else InputSource.WEBHOOK, {}
        )
        trigger_name = add_node(trigger_node, node_positions["x"], node_positions["y"])
        node_positions["x"] += 200

        # 2. Add rate limiting if needed
        prev_node = trigger_name
        if pattern.safety_controls and "rate_limiting" in pattern.safety_controls:
            rate_limiter = AINodeConfiguration.create_safety_node("rate_limiter")
            rate_limiter["name"] = "Rate Limiter"
            limiter_name = add_node(
                rate_limiter, node_positions["x"], node_positions["y"]
            )
            connections[prev_node] = {
                "main": [[{"node": limiter_name, "type": "main", "index": 0}]]
            }
            prev_node = limiter_name
            node_positions["x"] += 200

        # 3. Add PII detection if needed
        if pattern.safety_controls and "pii_protection" in pattern.safety_controls:
            pii_detector = AINodeConfiguration.create_safety_node("pii_detection")
            pii_detector["name"] = "PII Detection"
            pii_name = add_node(pii_detector, node_positions["x"], node_positions["y"])
            connections[prev_node] = {
                "main": [[{"node": pii_name, "type": "main", "index": 0}]]
            }
            prev_node = pii_name
            node_positions["x"] += 200

        # 4. Add memory node if needed
        memory_node_name = None
        if pattern.requires_memory:
            memory_node = MemoryNodeBuilder.create_buffer_memory()
            memory_node["name"] = "Conversation Memory"
            memory_node_name = add_node(
                memory_node, node_positions["x"], node_positions["y"] - 150
            )

        # 5. Add vector store if needed
        vector_node_name = None
        if pattern.vector_stores:
            vector_store = VectorStoreNodeBuilder.create_supabase_vector_node()
            vector_store["name"] = "Vector Store"
            vector_node_name = add_node(
                vector_store, node_positions["x"], node_positions["y"] + 150
            )

        # 6. Create main AI agent(s)
        if len(pattern.agent_types) == 1:
            # Single agent
            agent = AgentNodeBuilder.create_conversational_agent(
                name=f"{name} Agent",
                model_provider=pattern.ai_providers[0].value,
                model=config.get("suggested_models", {}).get("primary", "gpt-4"),
                memory_enabled=pattern.requires_memory,
                tools=self._get_tools_for_pattern(pattern, config),
            )
            agent_name = add_node(agent, node_positions["x"], node_positions["y"])
            connections[prev_node] = {
                "main": [[{"node": agent_name, "type": "main", "index": 0}]]
            }
            prev_node = agent_name
            node_positions["x"] += 200

        else:
            # Multi-agent setup
            agents = []
            for i, agent_type in enumerate(pattern.agent_types):
                agent_config = {
                    "name": f"{agent_type.value.replace('_', ' ').title()} Agent",
                    "model_provider": pattern.ai_providers[
                        min(i, len(pattern.ai_providers) - 1)
                    ].value,
                    "model": config.get("suggested_models", {}).get("primary", "gpt-4"),
                }
                agents.append(agent_config)

            multi_agent = create_multi_agent_workflow(
                agents=agents,
                coordinator_config={"objective": f"Complete {name} workflow"},
            )

            # Add all multi-agent nodes
            for node in multi_agent["nodes"]:
                node_name = add_node(
                    node, node_positions["x"] + node["position"][0], node["position"][1]
                )
                if i == 0:  # Connect trigger to first agent
                    connections[prev_node] = {
                        "main": [[{"node": node_name, "type": "main", "index": 0}]]
                    }

            # Add multi-agent connections
            connections.update(multi_agent["connections"])
            prev_node = multi_agent["nodes"][-1]["name"]
            node_positions["x"] += 400

        # 7. Add human approval if needed
        if pattern.human_in_loop:
            approval_node = AINodeConfiguration.create_safety_node("human_approval")
            approval_node["name"] = "Human Approval"
            approval_name = add_node(
                approval_node, node_positions["x"], node_positions["y"]
            )
            connections[prev_node] = {
                "main": [[{"node": approval_name, "type": "main", "index": 0}]]
            }
            prev_node = approval_name
            node_positions["x"] += 200

        # 8. Add output nodes
        for i, output in enumerate(pattern.outputs):
            output_node = self._create_output_node(output, node_positions["x"])
            output_name = add_node(
                output_node, node_positions["x"], node_positions["y"] + (i * 150)
            )
            if prev_node not in connections:
                connections[prev_node] = {"main": [[]]}
            connections[prev_node]["main"][0].append(
                {"node": output_name, "type": "main", "index": 0}
            )

        return {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "active": False,
            "settings": {
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "saveExecutionProgress": True,
                "callerPolicy": "workflowsFromSameOwner",
                "executionTimeout": 900,  # 15 minutes for AI workflows
            },
            "tags": [self.team_name, "ai-powered", f"pattern:{pattern.name}"],
        }

    def _get_tools_for_pattern(
        self, pattern: AIWorkflowPattern, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get appropriate tools for the AI pattern"""

        tools = []

        # Add tools based on pattern
        if "calculator" in config.get("suggested_tools", []):
            tools.append({"toolId": "@n8n/n8n-nodes-langchain.toolCalculator"})

        if "web_search" in config.get("suggested_tools", []):
            tools.append({"toolId": "@n8n/n8n-nodes-langchain.toolWebBrowser"})

        if "code" in config.get("suggested_tools", []):
            tools.append(
                {
                    "toolId": "@n8n/n8n-nodes-langchain.toolCode",
                    "language": "javaScript",
                }
            )

        if pattern.vector_stores:
            tools.append(
                {
                    "toolId": "@n8n/n8n-nodes-langchain.toolVectorStore",
                    "operation": "search",
                }
            )

        # Add MCP tools if configured
        if config.get("mcp_tools"):
            for mcp_tool in config["mcp_tools"]:
                tools.append(
                    {
                        "toolId": "@n8n/n8n-nodes-langchain.toolMcp",
                        "server": mcp_tool.get("server", "default"),
                        "tool": mcp_tool.get("tool", "default"),
                    }
                )

        return tools

    def _create_output_node(
        self, output: OutputChannel, x_position: int
    ) -> Dict[str, Any]:
        """Create an output node based on type"""

        if output == OutputChannel.EMAIL_GMAIL:
            return {
                "name": "Send Email",
                "type": "n8n-nodes-base.gmail",
                "typeVersion": 2.1,
                "parameters": {
                    "operation": "send",
                    "sendTo": "={{ $json.recipient }}",
                    "subject": "{{ $json.subject }}",
                    "message": "={{ $json.message }}",
                },
            }
        elif output == OutputChannel.SLACK:
            return {
                "name": "Send to Slack",
                "type": "n8n-nodes-base.slack",
                "typeVersion": 2.1,
                "parameters": {
                    "operation": "post",
                    "channel": "={{ $json.channel || '#general' }}",
                    "text": "={{ $json.message }}",
                },
            }
        else:
            return super()._create_notification_node(output.value, x_position)

    async def create_ai_workflow(
        self,
        description: str,
        name: str,
        team: str,
        category: str = "ai-automation",
        force_pattern: str = None,
    ) -> Dict[str, Any]:
        """Create an AI-powered workflow"""

        print(f"\n🤖 Analyzing AI requirements for: {description}")

        # Check if AI is needed
        ai_pattern, ai_config = await self.analyze_ai_requirements(description)

        if ai_pattern:
            print(f"✓ AI Pattern detected: {ai_pattern.name}")
            print(f"✓ AI Providers: {[p.value for p in ai_pattern.ai_providers]}")
            print(f"✓ Agent Types: {[a.value for a in ai_pattern.agent_types]}")

            # Generate AI workflow
            workflow = self.generate_ai_workflow_nodes(ai_pattern, ai_config, name)

            # Enhance with LLM
            enhanced_workflow = await self._enhance_workflow_with_llm(
                workflow, description, ai_pattern, ai_config
            )

            return {
                "workflow": enhanced_workflow,
                "metadata": {
                    "description": description,
                    "team": team,
                    "category": category,
                    "ai_pattern": ai_pattern.name,
                    "ai_config": ai_config,
                    "created_at": datetime.utcnow().isoformat(),
                    "is_ai_powered": True,
                },
            }
        else:
            print("ℹ️ No AI requirements detected, using standard workflow generation")
            # Fall back to standard workflow generation
            from tools.n8n_workflow_factory_v2 import EnhancedWorkflowFactory

            v2_factory = EnhancedWorkflowFactory(team)
            return await v2_factory.create_workflow(description, name, team, category)

    async def _enhance_workflow_with_llm(
        self,
        workflow: Dict[str, Any],
        description: str,
        pattern: AIWorkflowPattern,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use LLM to enhance and refine the generated workflow"""

        prompt = f"""You are an expert in n8n workflow design with deep knowledge of AI agents and LangChain integration.

I have generated a base AI workflow that needs enhancement:

Description: {description}
Pattern: {pattern.name}
Configuration: {json.dumps(config, indent=2)}

Current workflow structure:
{json.dumps(workflow, indent=2)}

Please enhance this workflow by:
1. Adding proper error handling nodes
2. Configuring node parameters with appropriate values
3. Adding data transformation nodes where needed
4. Ensuring proper connection flow
5. Adding logging and monitoring nodes
6. Setting up proper authentication placeholders
7. Adding any missing safety controls

Important guidelines:
- Use n8n v1.82+ node formats
- All AI nodes should use @n8n/n8n-nodes-langchain prefix
- Include proper error workflows
- Add webhook responses where appropriate
- Use expressions like {{{{ $json.field }}}} for dynamic values

Return the complete enhanced workflow JSON."""

        response = self.llm.invoke(prompt)
        enhanced_json = response.content

        # Clean and parse
        enhanced_json = re.sub(r"```json\n?", "", enhanced_json)
        enhanced_json = re.sub(r"\n?```", "", enhanced_json)

        try:
            enhanced_workflow = json.loads(enhanced_json)
            # Merge enhancements with original
            workflow.update(enhanced_workflow)
            return workflow
        except json.JSONDecodeError:
            print("⚠️ Could not parse LLM enhancements, using base workflow")
            return workflow

    async def create_from_template_with_ai(
        self, template_name: str, customization_prompt: str, name: str, team: str
    ) -> Dict[str, Any]:
        """Create a workflow from a template with AI customization"""

        # This would load from a curated template library
        # For now, we'll use the existing templates
        template = None
        for category in ["data-pipeline", "integration", "approval", "automation"]:
            try:
                template = get_template(category, template_name)
                break
            except ValueError:
                continue

        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Use AI to customize the template
        prompt = f"""You are customizing an n8n workflow template based on user requirements.

Template: {template_name}
Current workflow:
{json.dumps(template, indent=2)}

User requirements:
{customization_prompt}

Customize this template by:
1. Modifying node parameters to match the requirements
2. Adding or removing nodes as needed
3. Updating connections
4. Setting appropriate values for placeholders

Return the customized workflow JSON."""

        response = self.llm.invoke(prompt)
        customized = json.loads(response.content)

        return {
            "workflow": customized,
            "metadata": {
                "base_template": template_name,
                "customization": customization_prompt,
                "team": team,
                "created_at": datetime.utcnow().isoformat(),
            },
        }


def main():
    """Enhanced CLI with AI workflow support"""

    import argparse

    parser = argparse.ArgumentParser(description="AI-Enhanced N8N Workflow Factory")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create AI workflow command
    ai_parser = subparsers.add_parser("create-ai", help="Create an AI-powered workflow")
    ai_parser.add_argument("description", help="Natural language workflow description")
    ai_parser.add_argument("--name", required=True, help="Workflow name")
    ai_parser.add_argument("--team", required=True, help="Owner team")
    ai_parser.add_argument(
        "--category",
        default="ai-automation",
        choices=[
            "ai-automation",
            "ai-analysis",
            "ai-support",
            "ai-content",
            "ai-orchestration",
        ],
    )
    ai_parser.add_argument("--output", help="Output file path")

    # Customize template command
    template_parser = subparsers.add_parser(
        "customize-template", help="Customize a template with AI"
    )
    template_parser.add_argument("template", help="Template name")
    template_parser.add_argument("requirements", help="Customization requirements")
    template_parser.add_argument("--name", required=True, help="Workflow name")
    template_parser.add_argument("--team", required=True, help="Owner team")

    # List AI patterns command
    patterns_parser = subparsers.add_parser(
        "list-ai-patterns", help="List available AI patterns"
    )

    args = parser.parse_args()

    if args.command == "create-ai":
        factory = AIEnhancedWorkflowFactory(team_name=args.team)

        # Create AI workflow
        workflow_data = asyncio.run(
            factory.create_ai_workflow(
                description=args.description,
                name=args.name,
                team=args.team,
                category=args.category,
            )
        )

        # Display workflow
        print("\n📋 Generated AI Workflow:")
        print("=" * 80)
        print(json.dumps(workflow_data["workflow"], indent=2))
        print("=" * 80)

        # Save if output specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump(workflow_data["workflow"], f, indent=2)
            print(f"\n✓ Saved to: {args.output}")

        print("\n📊 Metadata:")
        for key, value in workflow_data["metadata"].items():
            print(f"  {key}: {value}")

    elif args.command == "customize-template":
        factory = AIEnhancedWorkflowFactory(team_name=args.team)

        workflow_data = asyncio.run(
            factory.create_from_template_with_ai(
                template_name=args.template,
                customization_prompt=args.requirements,
                name=args.name,
                team=args.team,
            )
        )

        print("\n📋 Customized Workflow:")
        print("=" * 80)
        print(json.dumps(workflow_data["workflow"], indent=2))

    elif args.command == "list-ai-patterns":
        patterns = [
            "ai_customer_support",
            "document_analysis_rag",
            "multi_agent_research",
            "ai_data_analyst",
            "content_generation_pipeline",
            "ai_workflow_orchestrator",
            "intelligent_form_processor",
            "ai_code_reviewer",
        ]

        print("\n🤖 Available AI Workflow Patterns:")
        print("=" * 40)
        for pattern in patterns:
            print(f"  - {pattern}")


if __name__ == "__main__":
    main()
