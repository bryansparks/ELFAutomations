#!/usr/bin/env python3
"""Test the LLM factory fallback system"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from elf_automations.shared.utils import LLMFactory


def main():
    print("🧪 Testing LLM Factory fallback system...")

    # Test 1: Try to create OpenAI (should fail and fallback)
    print("\n1️⃣ Attempting OpenAI GPT-4 with automatic fallback...")
    try:
        llm = LLMFactory.create_llm(
            preferred_provider="openai", preferred_model="gpt-4", team_name="test-team"
        )
        print(f"✅ Got LLM: {type(llm).__name__}")
        print(
            f"   Model: {llm.model_name if hasattr(llm, 'model_name') else 'unknown'}"
        )

        # Test it
        response = llm.invoke("Say 'Hello from fallback system!' in 5 words or less.")
        print(f"Response: {response.content}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Force Anthropic
    print("\n2️⃣ Testing Anthropic directly...")
    try:
        llm = LLMFactory.create_llm(
            preferred_provider="anthropic",
            preferred_model="claude-3-haiku-20240307",
            team_name="test-team",
        )
        print(f"✅ Got LLM: {type(llm).__name__}")

        # Test it
        response = llm.invoke("Say 'Anthropic works!' in 5 words or less.")
        print(f"Response: {response.content}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
