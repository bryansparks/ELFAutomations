"""
N8N Context Loader

Loads and manages N8N documentation, examples, and patterns for intelligent workflow generation.
Replicates Claude Project approach by maintaining rich context about N8N capabilities.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from supabase import Client


class N8NContextLoader:
    """Loads and manages N8N context for intelligent workflow generation"""

    def __init__(self, supabase_client: Client = None):
        self.supabase = supabase_client
        self.context_cache = {}
        self.documentation = {}
        self.examples = {}
        self.patterns = {}
        self.node_specs = {}

        # Initialize with built-in knowledge
        self._load_built_in_context()

    def _load_built_in_context(self):
        """Load built-in N8N knowledge"""

        # Node specifications
        self.node_specs = {
            "@n8n/n8n-nodes-langchain.agent": {
                "description": "AI agent that can use tools and maintain conversation",
                "categories": ["ai", "langchain"],
                "version": "1.5",
                "inputs": ["main"],
                "outputs": ["main"],
                "parameters": {
                    "agent": [
                        "conversationalAgent",
                        "toolsAgent",
                        "planAndExecuteAgent",
                        "reActAgent",
                    ],
                    "prompt": "System prompt for the agent",
                    "model": "AI model configuration",
                    "tools": "Optional tools for the agent",
                    "memory": "Optional memory configuration",
                    "options": {
                        "temperature": "0-1, controls randomness",
                        "maxIterations": "Maximum agent iterations",
                        "maxTokens": "Maximum tokens per response",
                    },
                },
                "best_practices": [
                    "Always set maxTokens to control costs",
                    "Use appropriate temperature for task",
                    "Add error handling for AI failures",
                    "Consider using memory for conversations",
                ],
            },
            "@n8n/n8n-nodes-langchain.vectorStore": {
                "description": "Vector store for semantic search and RAG",
                "categories": ["ai", "langchain", "storage"],
                "inputs": ["main"],
                "outputs": ["main"],
                "parameters": {
                    "operation": ["insert", "search", "delete"],
                    "vectorStore": "Type of vector store",
                    "embeddings": "Embedding model configuration",
                },
                "best_practices": [
                    "Use appropriate embedding model",
                    "Index metadata for filtering",
                    "Set appropriate similarity threshold",
                    "Consider chunking strategy for documents",
                ],
            },
            "@n8n/n8n-nodes-langchain.memory": {
                "description": "Memory for conversational AI",
                "categories": ["ai", "langchain"],
                "types": ["buffer", "window", "summary", "vector"],
                "best_practices": [
                    "Use window memory for long conversations",
                    "Summary memory for context compression",
                    "Vector memory for semantic retrieval",
                ],
            },
        }

        # Common patterns
        self.patterns = {
            "rag_pattern": {
                "name": "Retrieval Augmented Generation",
                "description": "Enhance AI responses with relevant context",
                "nodes": [
                    {"type": "documentLoader", "purpose": "Load documents"},
                    {"type": "textSplitter", "purpose": "Chunk documents"},
                    {"type": "embeddings", "purpose": "Create embeddings"},
                    {"type": "vectorStore", "purpose": "Store/search vectors"},
                    {"type": "agent", "purpose": "Generate response with context"},
                ],
                "example_use_cases": [
                    "Customer support with knowledge base",
                    "Document Q&A systems",
                    "Research assistants",
                ],
            },
            "multi_agent_pattern": {
                "name": "Multi-Agent Collaboration",
                "description": "Multiple specialized agents working together",
                "nodes": [
                    {
                        "type": "agent",
                        "role": "coordinator",
                        "purpose": "Orchestrate tasks",
                    },
                    {
                        "type": "agent",
                        "role": "researcher",
                        "purpose": "Gather information",
                    },
                    {"type": "agent", "role": "analyst", "purpose": "Analyze data"},
                    {"type": "agent", "role": "writer", "purpose": "Generate output"},
                ],
                "coordination_strategies": [
                    "Sequential execution",
                    "Parallel with merge",
                    "Hierarchical delegation",
                ],
            },
            "human_in_loop_pattern": {
                "name": "Human-in-the-Loop AI",
                "description": "AI with human approval/feedback",
                "nodes": [
                    {"type": "agent", "purpose": "Generate initial response"},
                    {"type": "wait", "purpose": "Wait for human review"},
                    {"type": "if", "purpose": "Check approval status"},
                    {"type": "agent", "purpose": "Refine based on feedback"},
                ],
                "use_cases": [
                    "Content generation with review",
                    "High-stakes decisions",
                    "Training data validation",
                ],
            },
        }

        # Best practices
        self.documentation["best_practices"] = {
            "ai_workflows": [
                "Always implement error handling for AI nodes",
                "Set token limits to control costs",
                "Use appropriate models for tasks (GPT-4 for complex, GPT-3.5 for simple)",
                "Implement caching for repeated queries",
                "Add logging for AI decisions",
                "Use structured output parsing",
                "Implement safety checks (content filtering, PII detection)",
            ],
            "performance": [
                "Use parallel execution where possible",
                "Implement pagination for large datasets",
                "Cache expensive operations",
                "Use batch processing for bulk operations",
                "Set appropriate timeouts",
                "Monitor execution times",
            ],
            "security": [
                "Never hardcode credentials",
                "Use HTTPS for external APIs",
                "Implement webhook authentication",
                "Validate all inputs",
                "Sanitize outputs",
                "Use least privilege principle",
            ],
            "cost_optimization": [
                "Use cheaper models when possible",
                "Implement response caching",
                "Batch API calls",
                "Set token limits",
                "Monitor usage metrics",
                "Use vector stores efficiently",
            ],
        }

        # Example workflows
        self.examples["ai_customer_support"] = {
            "description": "AI-powered customer support with email and Slack",
            "key_features": [
                "Multi-channel support",
                "Conversation memory",
                "Escalation to human",
                "Knowledge base integration",
            ],
            "nodes": [
                {
                    "type": "@n8n/n8n-nodes-langchain.agent",
                    "config": {
                        "agent": "conversationalAgent",
                        "model": "gpt-4",
                        "memory": "buffer",
                        "tools": ["vectorStore", "calculator"],
                    },
                }
            ],
        }

    async def load_from_supabase(self):
        """Load additional context from Supabase"""

        if not self.supabase:
            return

        try:
            # Load successful workflows as examples
            result = self.supabase.table("n8n_workflow_registry").select("*").execute()

            for workflow in result.data:
                if workflow.get("success_rate", 0) > 0.9:  # High success rate
                    self.examples[workflow["name"]] = {
                        "description": workflow.get("description", ""),
                        "category": workflow.get("category", ""),
                        "workflow_data": workflow.get("workflow_data", {}),
                    }

            # Load workflow patterns from successful executions
            pattern_result = (
                self.supabase.table("workflow_patterns").select("*").execute()
            )

            for pattern in pattern_result.data:
                self.patterns[pattern["name"]] = pattern

        except Exception as e:
            print(f"Error loading context from Supabase: {e}")

    def get_relevant_context(
        self, description: str, workflow_type: str = None
    ) -> Dict[str, Any]:
        """Get relevant context for a workflow description"""

        context = {
            "relevant_patterns": [],
            "similar_examples": [],
            "recommended_nodes": [],
            "best_practices": [],
            "warnings": [],
        }

        description_lower = description.lower()

        # Find relevant patterns
        for pattern_name, pattern_data in self.patterns.items():
            if any(
                keyword in description_lower
                for keyword in pattern_data.get("keywords", [])
            ):
                context["relevant_patterns"].append(pattern_data)

        # Find similar examples
        for example_name, example_data in self.examples.items():
            example_desc = example_data.get("description", "").lower()
            if any(word in description_lower for word in example_desc.split()):
                context["similar_examples"].append(
                    {"name": example_name, "data": example_data}
                )

        # Recommend nodes based on keywords
        if "ai" in description_lower or "agent" in description_lower:
            context["recommended_nodes"].append(
                {
                    "type": "@n8n/n8n-nodes-langchain.agent",
                    "reason": "AI capabilities detected in requirements",
                }
            )

        if "search" in description_lower or "knowledge" in description_lower:
            context["recommended_nodes"].append(
                {
                    "type": "@n8n/n8n-nodes-langchain.vectorStore",
                    "reason": "Search/knowledge base functionality needed",
                }
            )

        if "conversation" in description_lower or "chat" in description_lower:
            context["recommended_nodes"].append(
                {
                    "type": "@n8n/n8n-nodes-langchain.memory",
                    "reason": "Conversational context management needed",
                }
            )

        # Add relevant best practices
        if "ai" in description_lower:
            context["best_practices"].extend(
                self.documentation["best_practices"]["ai_workflows"]
            )

        if "performance" in description_lower or "fast" in description_lower:
            context["best_practices"].extend(
                self.documentation["best_practices"]["performance"]
            )

        # Add warnings
        if "credential" in description_lower or "password" in description_lower:
            context["warnings"].append(
                "Use n8n credentials system, never hardcode sensitive data"
            )

        if "unlimited" in description_lower or "all" in description_lower:
            context["warnings"].append(
                "Implement pagination and limits to prevent resource exhaustion"
            )

        return context

    def get_node_documentation(self, node_type: str) -> Dict[str, Any]:
        """Get documentation for a specific node type"""

        return self.node_specs.get(
            node_type,
            {
                "description": f"Documentation for {node_type}",
                "parameters": {},
                "best_practices": [],
            },
        )

    def get_pattern_template(self, pattern_name: str) -> Dict[str, Any]:
        """Get a workflow template for a pattern"""

        pattern = self.patterns.get(pattern_name, {})

        if not pattern:
            return {}

        # Generate a template workflow based on the pattern
        nodes = []
        connections = {}
        x_pos = 250

        for i, node_spec in enumerate(pattern.get("nodes", [])):
            node = {
                "id": f"node_{i}",
                "name": node_spec.get("purpose", f"Node {i}"),
                "type": self._get_node_type_for_purpose(node_spec.get("type", "")),
                "position": [x_pos, 300],
                "parameters": {},
            }
            nodes.append(node)

            # Connect to previous node
            if i > 0:
                prev_node = nodes[i - 1]["name"]
                connections[prev_node] = {
                    "main": [[{"node": node["name"], "type": "main", "index": 0}]]
                }

            x_pos += 200

        return {
            "name": f"{pattern_name} Template",
            "nodes": nodes,
            "connections": connections,
            "pattern_info": pattern,
        }

    def _get_node_type_for_purpose(self, purpose: str) -> str:
        """Map purpose to actual node type"""

        mapping = {
            "agent": "@n8n/n8n-nodes-langchain.agent",
            "vectorStore": "@n8n/n8n-nodes-langchain.vectorStore",
            "memory": "@n8n/n8n-nodes-langchain.memory",
            "documentLoader": "@n8n/n8n-nodes-langchain.documentLoader",
            "textSplitter": "@n8n/n8n-nodes-langchain.textSplitter",
            "embeddings": "@n8n/n8n-nodes-langchain.embeddings",
            "wait": "n8n-nodes-base.wait",
            "if": "n8n-nodes-base.if",
        }

        return mapping.get(purpose, "n8n-nodes-base.noOp")

    def learn_from_workflow(
        self, workflow: Dict[str, Any], execution_result: Dict[str, Any]
    ):
        """Learn from workflow execution results"""

        if not self.supabase:
            return

        try:
            # Extract patterns from successful workflows
            if execution_result.get("success", False):
                pattern_data = {
                    "workflow_id": workflow.get("id"),
                    "node_sequence": [n["type"] for n in workflow.get("nodes", [])],
                    "execution_time": execution_result.get("execution_time"),
                    "cost": execution_result.get("cost", 0),
                    "learned_at": datetime.utcnow().isoformat(),
                }

                # Store in cache for immediate use
                cache_key = f"learned_{workflow.get('name', 'unknown')}"
                self.context_cache[cache_key] = pattern_data

                # Optionally store in Supabase for persistence
                # self.supabase.table("learned_patterns").insert(pattern_data).execute()

        except Exception as e:
            print(f"Error learning from workflow: {e}")

    def get_cost_estimate(self, nodes: List[Dict[str, Any]]) -> float:
        """Estimate cost for a set of nodes"""

        total_cost = 0.0

        for node in nodes:
            node_type = node.get("type", "")

            # AI nodes are most expensive
            if "@n8n/n8n-nodes-langchain.agent" in node_type:
                model = (
                    node.get("parameters", {})
                    .get("model", {})
                    .get("modelName", "gpt-3.5-turbo")
                )
                if "gpt-4" in model:
                    total_cost += 0.03  # Approximate GPT-4 cost
                else:
                    total_cost += 0.002  # Approximate GPT-3.5 cost

            elif "@n8n/n8n-nodes-langchain.vectorStore" in node_type:
                total_cost += 0.001  # Vector operations

            elif "httpRequest" in node_type:
                total_cost += 0.0001  # API calls

            elif "postgres" in node_type or "supabase" in node_type:
                total_cost += 0.0005  # Database operations

        return total_cost


class WorkflowContextEnhancer:
    """Enhances workflow generation with contextual knowledge"""

    def __init__(self, context_loader: N8NContextLoader):
        self.context_loader = context_loader

    def enhance_prompt(self, base_prompt: str, description: str) -> str:
        """Enhance a prompt with relevant context"""

        context = self.context_loader.get_relevant_context(description)

        enhanced_prompt = f"""{base_prompt}

## Relevant Context:

### Similar Examples:
{json.dumps(context['similar_examples'], indent=2)}

### Recommended Patterns:
{json.dumps(context['relevant_patterns'], indent=2)}

### Recommended Nodes:
{json.dumps(context['recommended_nodes'], indent=2)}

### Best Practices to Follow:
{chr(10).join(f"- {bp}" for bp in context['best_practices'])}

### Important Warnings:
{chr(10).join(f"⚠️ {warning}" for warning in context['warnings'])}

Consider this context when generating the workflow."""

        return enhanced_prompt

    def validate_workflow(self, workflow: Dict[str, Any]) -> List[str]:
        """Validate workflow against best practices"""

        issues = []
        nodes = workflow.get("nodes", [])

        # Check AI nodes
        ai_nodes = [n for n in nodes if "@n8n/n8n-nodes-langchain" in n.get("type", "")]

        for node in ai_nodes:
            params = node.get("parameters", {})

            # Check for token limits
            if "agent" in node.get("type", "") and not params.get("options", {}).get(
                "maxTokens"
            ):
                issues.append(f"AI agent '{node.get('name')}' missing maxTokens limit")

            # Check for error handling
            node_name = node.get("name", node.get("id"))
            connections = workflow.get("connections", {})
            if (
                node_name not in connections
                or len(connections.get(node_name, {}).get("main", [[]])) < 2
            ):
                issues.append(f"AI node '{node_name}' missing error handling")

        # Check for hardcoded credentials
        workflow_str = json.dumps(workflow)
        if any(
            secret in workflow_str.lower()
            for secret in ["password", "api_key", "secret"]
        ):
            issues.append("Potential hardcoded credentials detected")

        return issues


# Example usage
if __name__ == "__main__":
    # Initialize context loader
    loader = N8NContextLoader()

    # Get context for a workflow
    context = loader.get_relevant_context(
        "Create an AI customer support workflow that uses RAG to answer questions"
    )

    print("Relevant Context:")
    print(json.dumps(context, indent=2))

    # Get pattern template
    template = loader.get_pattern_template("rag_pattern")
    print("\nRAG Pattern Template:")
    print(json.dumps(template, indent=2))
