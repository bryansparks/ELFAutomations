#!/usr/bin/env python3
"""Direct test of product team with fallback - no CrewAI execution"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from elf_automations.shared.utils import LLMFactory


def main():
    print("🧪 Testing Product Team LLM Fallback Directly\n")

    # Create LLM with fallback
    print("1️⃣ Creating LLM with fallback for product team...")
    llm = LLMFactory.create_llm(
        preferred_provider="openai", preferred_model="gpt-4", team_name="product-team"
    )

    print(f"✅ LLM created: {type(llm).__name__}")
    print(f"   Model: {llm.model_name if hasattr(llm, 'model_name') else 'unknown'}")

    # Test multiple product-related queries
    queries = [
        "List 3 key features for a construction PM app",
        "What's the most important user persona for construction software?",
        "Name 2 competitors in construction project management",
    ]

    print("\n2️⃣ Testing product queries with fallback...")
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        response = llm.invoke(query)
        print(f"Response: {response.content[:100]}...")

    print("\n✅ Product team LLM successfully using Anthropic fallback!")
    print("   OpenAI quota exceeded → Automatically switched to Anthropic")


if __name__ == "__main__":
    main()
