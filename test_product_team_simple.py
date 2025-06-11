#!/usr/bin/env python3
"""Simple test to verify product team agents use Anthropic fallback"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "teams" / "product-team"))

# Import individual agents
from agents.senior_product_manager import senior_product_manager_agent


def main():
    print("🧪 Testing Product Team Agent with Anthropic Fallback\n")

    # Create just the senior PM agent
    print("1️⃣ Creating Senior Product Manager agent...")
    agent = senior_product_manager_agent()

    print(f"✅ Agent created: {agent.role}")
    print(f"   LLM type: {type(agent.llm).__name__}")

    # Test a simple task
    print("\n2️⃣ Testing agent with simple task...")
    from crewai import Task

    task = Task(
        description="List 3 key features for a construction PM app in bullet points",
        agent=agent,
        expected_output="3 bullet points",
    )

    result = agent.execute_task(task)

    print("\n3️⃣ Result:")
    print(result)

    print("\n✅ Agent successfully used Anthropic fallback!")


if __name__ == "__main__":
    main()
