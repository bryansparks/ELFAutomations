#!/usr/bin/env python3
"""
Test script to diagnose LangChain import issues
"""

import sys

print(f"Python version: {sys.version}")
print("\nTesting LangChain imports...\n")

# Test 1: Basic imports
print("1. Testing basic imports:")
try:
    import langchain

    print(f"   ✓ langchain version: {langchain.__version__}")
except ImportError as e:
    print(f"   ✗ langchain import failed: {e}")

try:
    import langchain_core

    print(f"   ✓ langchain_core version: {langchain_core.__version__}")
except ImportError as e:
    print(f"   ✗ langchain_core import failed: {e}")

# Test 2: Provider imports
print("\n2. Testing provider imports:")
try:
    from langchain_openai import ChatOpenAI

    print("   ✓ langchain_openai.ChatOpenAI imported successfully")
except ImportError as e:
    print(f"   ✗ langchain_openai.ChatOpenAI import failed: {e}")

try:
    from langchain_anthropic import ChatAnthropic

    print("   ✓ langchain_anthropic.ChatAnthropic imported successfully")
except ImportError as e:
    print(f"   ✗ langchain_anthropic.ChatAnthropic import failed: {e}")

# Test 3: Core message imports
print("\n3. Testing core message imports:")
try:
    from langchain_core.messages import BaseMessage

    print("   ✓ langchain_core.messages.BaseMessage imported successfully")
except ImportError as e:
    print(f"   ✗ langchain_core.messages.BaseMessage import failed: {e}")

# Test 4: The problematic import
print("\n4. Testing for LangSmithParams (the problematic import):")
try:
    from langchain_core.language_models.chat_models import LangSmithParams

    print("   ✓ LangSmithParams imported successfully")
except ImportError as e:
    print(f"   ✗ LangSmithParams import failed: {e}")
    print("\n   This is expected - LangSmithParams might not exist in your version")

# Test 5: Check what's actually in the module
print("\n5. Checking available imports in langchain_core.language_models:")
try:
    import langchain_core.language_models as lm

    available = [attr for attr in dir(lm) if not attr.startswith("_")]
    print(f"   Available: {', '.join(available[:10])}")
    if len(available) > 10:
        print(f"   ... and {len(available) - 10} more")
except Exception as e:
    print(f"   ✗ Could not inspect module: {e}")

# Test 6: Check if this is coming from a specific file
print("\n6. Checking your LLM factory imports:")
try:
    from elf_automations.shared.utils.llm_factory import LLMFactory

    print("   ✓ LLMFactory imported successfully")
except ImportError as e:
    print(f"   ✗ LLMFactory import failed: {e}")
    print("\n   This might be the source of the LangSmithParams error")
