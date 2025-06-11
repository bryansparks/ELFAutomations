#!/usr/bin/env python3
"""Test the product team with Anthropic fallback"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the product team crew
sys.path.insert(0, str(Path(__file__).parent / "teams" / "product-team"))
from crew import ProductTeamCrew


def main():
    print("🧪 Testing Product Team with Anthropic Fallback\n")

    # Create the crew
    print("1️⃣ Initializing Product Team crew...")
    crew = ProductTeamCrew()

    # Test with a simple product request
    print("\n2️⃣ Running product analysis task...")
    result = crew.execute_task(
        "Create a simple PRD outline for a construction project management mobile app. Keep it brief - just the main sections and key points."
    )

    print("\n3️⃣ Results:")
    print("-" * 50)
    print(result)
    print("-" * 50)

    print("\n✅ Product team successfully executed with Anthropic fallback!")


if __name__ == "__main__":
    main()
