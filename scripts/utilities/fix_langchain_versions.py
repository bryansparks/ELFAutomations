#!/usr/bin/env python3
"""
Script to fix LangChain version compatibility issues

This script will:
1. Uninstall the current langchain packages
2. Install compatible versions
3. Verify the installation
"""

import subprocess
import sys


def run_command(cmd):
    """Run a command and print output"""
    print(f"\n>>> Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"ERROR: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR running command: {e}")
        return False


def main():
    print("=== LangChain Version Fix Script ===")
    print("\nThis script will fix the LangChain version compatibility issues.")

    # Ask for confirmation
    response = input("\nProceed with fixing LangChain versions? (y/n): ")
    if response.lower() != "y":
        print("Aborted.")
        return

    # Step 1: Uninstall existing packages
    print("\n1. Uninstalling existing LangChain packages...")
    packages_to_uninstall = [
        "langchain",
        "langchain-core",
        "langchain-community",
        "langchain-openai",
        "langchain-anthropic",
        "langchain-experimental",
        "langsmith",
    ]

    for package in packages_to_uninstall:
        run_command(f"pip uninstall -y {package}")

    # Step 2: Install compatible versions
    print("\n2. Installing compatible LangChain versions...")

    # Install in the correct order to avoid dependency conflicts
    install_commands = [
        # Core packages first
        "pip install langchain-core>=0.3.0",
        "pip install langchain>=0.3.0",
        "pip install langchain-community>=0.3.0",
        # Provider-specific packages
        "pip install langchain-openai>=0.2.0",
        "pip install langchain-anthropic>=0.2.0",
        # Additional packages
        "pip install langsmith>=0.1.80",
        "pip install langgraph>=0.2.0",
    ]

    for cmd in install_commands:
        if not run_command(cmd):
            print(
                f"\nERROR: Failed to install. You may need to manually resolve dependencies."
            )
            return

    # Step 3: Verify installation
    print("\n3. Verifying installation...")
    run_command("pip list | grep -i langchain")
    run_command("pip list | grep -i langsmith")

    # Step 4: Test import
    print("\n4. Testing imports...")
    test_code = """
import sys
try:
    from langchain_openai import ChatOpenAI
    print("✓ langchain_openai import successful")
except ImportError as e:
    print(f"✗ langchain_openai import failed: {e}")
    sys.exit(1)

try:
    from langchain_anthropic import ChatAnthropic
    print("✓ langchain_anthropic import successful")
except ImportError as e:
    print(f"✗ langchain_anthropic import failed: {e}")
    sys.exit(1)

try:
    from langchain_core.messages import BaseMessage
    print("✓ langchain_core import successful")
except ImportError as e:
    print(f"✗ langchain_core import failed: {e}")
    sys.exit(1)

print("\\nAll imports successful!")
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code], capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("\n✅ LangChain version fix completed successfully!")
        print("\nYou can now run your ElfAutomations code without import errors.")
    else:
        print("\n❌ There were errors during the fix process.")
        print("Please check the output above and resolve any issues manually.")


if __name__ == "__main__":
    main()
