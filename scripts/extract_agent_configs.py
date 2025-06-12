#!/usr/bin/env python3
"""
Extract current agent configurations from Kubernetes and generate YAML files
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from kubernetes import client, config


def load_k8s_config():
    """Load Kubernetes configuration"""
    try:
        # Try to load in-cluster config first
        config.load_incluster_config()
        print("Loaded in-cluster Kubernetes configuration")
    except:
        try:
            # Fall back to local kubeconfig
            config.load_kube_config()
            print("Loaded local Kubernetes configuration")
        except Exception as e:
            print(f"Failed to load Kubernetes configuration: {e}")
            sys.exit(1)


def get_agents(namespace="elf-automations"):
    """Get all agents from Kubernetes"""
    try:
        # Use CustomObjectsApi for CRDs
        api = client.CustomObjectsApi()

        # Get agents
        agents = api.list_namespaced_custom_object(
            group="kagent.dev", version="v1alpha1", namespace=namespace, plural="agents"
        )

        return agents.get("items", [])
    except Exception as e:
        print(f"Error getting agents: {e}")
        return []


def get_teams(namespace="elf-automations"):
    """Get all teams/crews from Kubernetes"""
    try:
        api = client.CustomObjectsApi()

        teams = api.list_namespaced_custom_object(
            group="kagent.dev", version="v1alpha1", namespace=namespace, plural="teams"
        )

        return teams.get("items", [])
    except Exception as e:
        print(f"Error getting teams: {e}")
        return []


def clean_agent_config(agent):
    """Clean agent configuration for YAML export"""
    # Remove Kubernetes-managed fields
    cleaned = {
        "apiVersion": agent.get("apiVersion", "kagent.dev/v1alpha1"),
        "kind": agent.get("kind", "Agent"),
        "metadata": {
            "name": agent["metadata"]["name"],
            "namespace": agent["metadata"]["namespace"],
            "labels": agent["metadata"].get("labels", {}),
        },
        "spec": agent.get("spec", {}),
    }

    # Remove status and other runtime fields
    if "status" in cleaned:
        del cleaned["status"]

    # Remove managed fields from metadata
    metadata_fields_to_remove = [
        "creationTimestamp",
        "generation",
        "resourceVersion",
        "uid",
        "managedFields",
        "finalizers",
    ]
    for field in metadata_fields_to_remove:
        if field in cleaned["metadata"]:
            del cleaned["metadata"][field]

    return cleaned


def save_agent_config(agent, base_path):
    """Save agent configuration to appropriate YAML file"""
    name = agent["metadata"]["name"]
    department = agent["metadata"].get("labels", {}).get("department", "unknown")

    # Create department directory if it doesn't exist
    dept_path = base_path / "agents" / department
    dept_path.mkdir(parents=True, exist_ok=True)

    # Clean the configuration
    cleaned_config = clean_agent_config(agent)

    # Save to YAML file
    config_file = dept_path / f"{name}.yaml"
    with open(config_file, "w") as f:
        yaml.dump(cleaned_config, f, default_flow_style=False, sort_keys=False)

    print(f"Saved agent config: {config_file}")
    return config_file


def save_team_config(team, base_path):
    """Save team/crew configuration to YAML file"""
    name = team["metadata"]["name"]

    # Create crews directory if it doesn't exist
    crews_path = base_path / "crews"
    crews_path.mkdir(parents=True, exist_ok=True)

    # Clean the configuration (similar to agent cleaning)
    cleaned_config = clean_agent_config(team)  # Same cleaning logic
    cleaned_config["kind"] = "Team"

    # Save to YAML file
    config_file = crews_path / f"{name}.yaml"
    with open(config_file, "w") as f:
        yaml.dump(cleaned_config, f, default_flow_style=False, sort_keys=False)

    print(f"Saved team config: {config_file}")
    return config_file


def create_templates(base_path):
    """Create template files for new agents and crews"""
    templates_path = base_path / "templates"
    templates_path.mkdir(parents=True, exist_ok=True)

    # Agent template
    agent_template = {
        "apiVersion": "kagent.dev/v1alpha1",
        "kind": "Agent",
        "metadata": {
            "name": "agent-name",
            "namespace": "elf-automations",
            "labels": {
                "app": "elf-automations",
                "component": "agent",
                "department": "department-name",
                "agent-type": "agent-type",
                "version": "v1.0.0",
            },
        },
        "spec": {
            "description": "Agent description",
            "systemMessage": "Detailed system prompt and instructions",
            "modelConfig": "anthropic-claude",
            "tools": [],
            "resources": {
                "requests": {"memory": "256Mi", "cpu": "100m"},
                "limits": {"memory": "512Mi", "cpu": "200m"},
            },
        },
    }

    # Team template
    team_template = {
        "apiVersion": "kagent.dev/v1alpha1",
        "kind": "Team",
        "metadata": {
            "name": "crew-name",
            "namespace": "elf-automations",
            "labels": {
                "app": "elf-automations",
                "component": "crew",
                "department": "department-name",
            },
        },
        "spec": {
            "description": "Crew description",
            "agents": [
                {"name": "agent-1", "role": "Primary role"},
                {"name": "agent-2", "role": "Secondary role"},
            ],
            "workflow": {
                "type": "sequential",
                "steps": [
                    {"agent": "agent-1", "task": "Task description"},
                    {"agent": "agent-2", "task": "Task description"},
                ],
            },
        },
    }

    # Save templates
    with open(templates_path / "agent-template.yaml", "w") as f:
        yaml.dump(agent_template, f, default_flow_style=False, sort_keys=False)

    with open(templates_path / "crew-template.yaml", "w") as f:
        yaml.dump(team_template, f, default_flow_style=False, sort_keys=False)

    print(f"Created templates in {templates_path}")


def main():
    """Main extraction function"""
    print("🔄 Extracting Agent Mesh configurations...")

    # Load Kubernetes config
    load_k8s_config()

    # Set up paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "agent-configs"
    config_path.mkdir(exist_ok=True)

    # Get current agents and teams
    agents = get_agents()
    teams = get_teams()

    print(f"Found {len(agents)} agents and {len(teams)} teams")

    # Extract agent configurations
    agent_files = []
    for agent in agents:
        try:
            config_file = save_agent_config(agent, config_path)
            agent_files.append(config_file)
        except Exception as e:
            print(f"Error saving agent {agent['metadata']['name']}: {e}")

    # Extract team configurations
    team_files = []
    for team in teams:
        try:
            config_file = save_team_config(team, config_path)
            team_files.append(config_file)
        except Exception as e:
            print(f"Error saving team {team['metadata']['name']}: {e}")

    # Create templates
    create_templates(config_path)

    # Create summary
    summary = {
        "extraction_date": datetime.now().isoformat(),
        "agents_extracted": len(agent_files),
        "teams_extracted": len(team_files),
        "agent_files": [str(f.relative_to(project_root)) for f in agent_files],
        "team_files": [str(f.relative_to(project_root)) for f in team_files],
    }

    with open(config_path / "extraction_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Configuration extraction complete!")
    print(f"📁 Configurations saved to: {config_path}")
    print(f"📊 Summary: {len(agent_files)} agents, {len(team_files)} teams")
    print(f"📋 See extraction_summary.json for details")


if __name__ == "__main__":
    main()
