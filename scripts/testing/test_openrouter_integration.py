#!/usr/bin/env python3
"""
Test OpenRouter Integration

Tests the ChatOpenRouter provider and LLMFactory integration.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from elf_automations.shared.utils.llm_factory import LLMFactory
from elf_automations.shared.utils.providers.openrouter import ChatOpenRouter
from langchain.schema import HumanMessage, SystemMessage
from rich.console import Console
from rich.table import Table

console = Console()


def test_direct_openrouter():
    """Test direct ChatOpenRouter usage"""
    console.print("\n[bold cyan]Testing Direct OpenRouter Usage[/bold cyan]\n")

    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        console.print("[red]OPENROUTER_API_KEY not set. Skipping direct test.[/red]")
        return

    try:
        # Create OpenRouter instance with auto routing
        llm = ChatOpenRouter(
            model="auto",
            preferences={"max_cost_per_token": 0.0001, "prefer_faster": True},
        )

        # Test with simple prompt
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is 2+2? Answer in one word."),
        ]

        console.print("[yellow]Sending request to OpenRouter (auto mode)...[/yellow]")
        response = llm._generate(messages)

        console.print(f"[green]Response:[/green] {response.content}")
        console.print(
            f"[blue]Model used:[/blue] {response.additional_kwargs.get('model_used', 'unknown')}"
        )

        # Show metadata
        if "openrouter_metadata" in response.additional_kwargs:
            metadata = response.additional_kwargs["openrouter_metadata"]
            console.print(
                f"[blue]Routing reason:[/blue] {metadata.get('routing_reason', 'N/A')}"
            )
            console.print(f"[blue]Cost:[/blue] ${metadata.get('cost', 0):.6f}")

    except Exception as e:
        console.print(f"[red]Error in direct test: {e}[/red]")


def test_llm_factory_integration():
    """Test LLMFactory with OpenRouter"""
    console.print("\n[bold cyan]Testing LLMFactory Integration[/bold cyan]\n")

    # Create table for results
    table = Table(title="LLM Factory Test Results")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Response", style="yellow")

    # Test configurations
    test_configs = [
        ("openrouter", "auto", "OpenRouter Auto"),
        ("openrouter", "gpt-3.5-turbo", "OpenRouter GPT-3.5"),
        ("local", "llama3-8b", "Local Llama3"),
        ("openai", "gpt-3.5-turbo", "Direct OpenAI"),
    ]

    for provider, model, desc in test_configs:
        try:
            console.print(f"\n[yellow]Testing {desc}...[/yellow]")

            llm = LLMFactory.create_llm(
                preferred_provider=provider,
                preferred_model=model,
                team_name="test-team",
                enable_fallback=True,
            )

            # For testing, we'll just verify creation
            table.add_row(provider, model, "✅ Created", f"{llm.__class__.__name__}")

        except Exception as e:
            table.add_row(provider, model, "❌ Failed", str(e)[:50] + "...")

    console.print(table)


def test_fallback_chain():
    """Test the fallback chain with OpenRouter"""
    console.print("\n[bold cyan]Testing Fallback Chain[/bold cyan]\n")

    # Show current fallback chain
    console.print("[yellow]Current fallback chain:[/yellow]")
    for i, (provider, model, temp) in enumerate(LLMFactory.FALLBACK_CHAIN):
        console.print(f"  {i+1}. {provider}/{model} (temp={temp})")

    # Create LLM with fallback enabled
    try:
        llm = LLMFactory.create_llm(
            preferred_provider="openrouter",
            preferred_model="auto",
            team_name="fallback-test",
            enable_fallback=True,
        )

        console.print(
            f"\n[green]Successfully created LLM:[/green] {type(llm).__name__}"
        )

    except Exception as e:
        console.print(f"\n[red]Failed to create LLM: {e}[/red]")


def show_configuration():
    """Show current configuration"""
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")

    config_table = Table(title="Environment Variables")
    config_table.add_column("Variable", style="cyan")
    config_table.add_column("Status", style="green")
    config_table.add_column("Value", style="yellow")

    env_vars = [
        "OPENROUTER_API_KEY",
        "OPENROUTER_DEFAULT_MODEL",
        "OPENROUTER_PREFERENCES",
        "LOCAL_MODEL_URL",
        "LLM_ROUTING_STRATEGY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                # Mask API keys
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                config_table.add_row(var, "✅ Set", masked)
            else:
                config_table.add_row(
                    var, "✅ Set", value[:50] + "..." if len(value) > 50 else value
                )
        else:
            config_table.add_row(var, "❌ Not set", "-")

    console.print(config_table)


def main():
    """Run all tests"""
    console.print("[bold magenta]OpenRouter Integration Test Suite[/bold magenta]")

    # Show configuration
    show_configuration()

    # Run tests
    test_direct_openrouter()
    test_llm_factory_integration()
    test_fallback_chain()

    console.print("\n[bold green]✅ Test suite completed![/bold green]")

    # Show next steps
    console.print("\n[bold yellow]Next Steps:[/bold yellow]")
    console.print("1. Set OPENROUTER_API_KEY environment variable")
    console.print("2. Configure LOCAL_MODEL_URL for local models")
    console.print("3. Update team configurations to use OpenRouter")
    console.print("4. Monitor costs and routing decisions")


if __name__ == "__main__":
    main()
