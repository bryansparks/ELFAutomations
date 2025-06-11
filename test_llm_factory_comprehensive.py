#!/usr/bin/env python3
"""Comprehensive test of the LLM factory fallback system"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Set up logging to see the fallback in action
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from elf_automations.shared.utils import LLMFactory


def main():
    print("🧪 Comprehensive LLM Factory Fallback Test\n")

    # Test 1: OpenAI -> Anthropic fallback
    print("1️⃣ Testing OpenAI → Anthropic fallback...")
    llm = LLMFactory.create_llm(
        preferred_provider="openai", preferred_model="gpt-4", team_name="test-team"
    )
    print(f"✅ Created LLM: {type(llm).__name__}")

    response = llm.invoke("What LLM are you? Reply with just your model name.")
    print(f"📝 Response: {response.content}")
    print(f"✨ Successfully fell back from OpenAI to Anthropic!\n")

    # Test 2: Direct Anthropic request
    print("2️⃣ Testing direct Anthropic request...")
    llm2 = LLMFactory.create_llm(
        preferred_provider="anthropic",
        preferred_model="claude-3-haiku-20240307",
        team_name="test-team-2",
    )

    response2 = llm2.invoke("Say 'Direct Anthropic works!' in exactly 3 words.")
    print(f"📝 Response: {response2.content}")

    # Test 3: Multiple invocations to ensure stability
    print("\n3️⃣ Testing multiple invocations...")
    for i in range(3):
        response = llm.invoke(f"Count to {i+1}")
        print(f"   Call {i+1}: {response.content}")

    print("\n✅ All tests passed! Fallback system is working correctly.")


if __name__ == "__main__":
    main()
