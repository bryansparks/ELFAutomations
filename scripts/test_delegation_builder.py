#!/usr/bin/env python3
"""
Test script for the DelegationBuilder functionality.
Demonstrates how chat conversations are analyzed and converted to task delegations.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.elf_automations.elf_automations.shared.chat import (
    DelegationBuilder,
    DelegationSpec,
)


def test_delegation_builder():
    """Test the delegation builder with a sample conversation."""

    print("🚀 Testing DelegationBuilder\n")

    # Create builder
    builder = DelegationBuilder()

    # Sample conversation messages
    messages = [
        {
            "role": "assistant",
            "content": "Hello! I'm the CEO of the executive team. How can I help you today?",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "role": "user",
            "content": "I need help creating a new marketing campaign for our product launch next month. We need social media content, email templates, and a landing page.",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "role": "assistant",
            "content": "I understand you need a comprehensive marketing campaign for your product launch. Let me clarify a few things: What's the target audience for this campaign? And what's the main message you want to convey?",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "role": "user",
            "content": "The target audience is tech-savvy professionals aged 25-40. The main message should focus on how our product saves time and increases productivity. We must launch by the 15th of next month. Also, please ensure the branding is consistent across all materials.",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "role": "assistant",
            "content": "Perfect! I have a clear picture now. You need a marketing campaign targeting tech professionals that emphasizes time-saving and productivity benefits. The campaign should include social media content, email templates, and a landing page, all with consistent branding, ready by the 15th. I can delegate this to our marketing team.",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "role": "user",
            "content": "Yes, exactly! Also, please make sure to avoid using any stock photos - we want original graphics only. And the budget should not exceed $10,000.",
            "timestamp": datetime.utcnow().isoformat(),
        },
    ]

    # Analyze the conversation
    session_id = "test-session-123"
    user_id = "test-user"

    print("📝 Analyzing conversation...")
    spec = builder.analyze_conversation(messages, session_id, user_id)

    # Display results
    print("\n✨ Delegation Spec Generated:\n")
    print(f"Title: {spec.title}")
    print(f"Description: {spec.description[:200]}...")
    print(f"Priority: {spec.priority.value}")
    print(f"Confidence Level: {spec.confidence_level:.2f}")
    print(f"Estimated Hours: {spec.estimated_hours}")
    print(f"Deadline: {spec.deadline}")

    print("\n📋 Requirements:")
    for i, req in enumerate(spec.requirements, 1):
        print(f"  {i}. {req.description}")
        print(f"     - Category: {req.category or 'general'}")
        print(f"     - Confidence: {req.confidence:.2f}")

    print("\n🚫 Constraints:")
    for constraint in spec.constraints:
        print(f"  - {constraint}")

    print("\n✅ Success Criteria:")
    for criteria in spec.success_criteria:
        print(f"  - {criteria}")

    print("\n👥 Suggested Teams:")
    for team in spec.suggested_teams:
        print(f"  - {team}")

    # Test delegation message creation
    print("\n📬 Creating A2A Delegation Message...")
    delegation_msg = builder.prepare_delegation_message(spec)

    print(f"\nMessage Type: ChatDelegationReady")
    print(f"Session ID: {delegation_msg.session_id}")
    print(f"Confidence: {delegation_msg.confidence_level:.2f}")
    print(f"Estimated Effort: {delegation_msg.estimated_effort}")
    print(f"Requires Confirmation: {delegation_msg.requires_user_confirmation}")

    # Test modifications
    print("\n🔧 Testing User Modifications...")
    modifications = {
        "priority": "urgent",
        "requirements": ["Include A/B testing for email campaigns"],
        "deadline": datetime.utcnow() + timedelta(days=20),
    }

    updated_spec = builder.update_spec_with_modifications(session_id, modifications)
    if updated_spec:
        print(f"Updated Priority: {updated_spec.priority.value}")
        print(f"New Requirement Added: {updated_spec.requirements[-1].description}")
        print(f"Updated Deadline: {updated_spec.deadline}")

    # Convert to task request
    print("\n📤 Converting to Task Request...")
    task_request = spec.to_task_request(
        from_agent="chat_interface", to_agent="executive-team-manager"
    )

    print(f"Task Type: {task_request.task_type}")
    print(f"From: {task_request.from_agent}")
    print(f"To: {task_request.to_agent}")
    print(f"Timeout: {task_request.timeout} seconds")

    print("\n✅ Test completed successfully!")


def test_edge_cases():
    """Test edge cases and different conversation patterns."""

    print("\n\n🧪 Testing Edge Cases\n")

    builder = DelegationBuilder()

    # Test 1: Very short conversation
    print("1️⃣ Testing short conversation...")
    short_messages = [
        {
            "role": "user",
            "content": "Fix the login bug",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]

    spec1 = builder.analyze_conversation(short_messages, "session-1", "user-1")
    print(f"   Title: {spec1.title}")
    print(f"   Confidence: {spec1.confidence_level:.2f}")
    print(f"   Suggested Teams: {spec1.suggested_teams}")

    # Test 2: Urgent request
    print("\n2️⃣ Testing urgent request...")
    urgent_messages = [
        {
            "role": "user",
            "content": "URGENT: The production server is down! We need to fix this immediately!",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "role": "assistant",
            "content": "I understand this is critical. Let me get the engineering team on this right away.",
            "timestamp": datetime.utcnow().isoformat(),
        },
    ]

    spec2 = builder.analyze_conversation(urgent_messages, "session-2", "user-2")
    print(f"   Priority: {spec2.priority.value}")
    print(f"   Estimated Hours: {spec2.estimated_hours}")

    # Test 3: Complex requirements
    print("\n3️⃣ Testing complex requirements...")
    complex_messages = [
        {
            "role": "user",
            "content": """I need a complete refactor of our authentication system.
            Requirements:
            - Must support OAuth2 and SAML
            - Should integrate with our existing user database
            - Need audit logging for all auth events
            - Must be GDPR compliant
            - Cannot break existing API endpoints

            Success criteria: All tests pass, no downtime during migration""",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]

    spec3 = builder.analyze_conversation(complex_messages, "session-3", "user-3")
    print(f"   Requirements Found: {len(spec3.requirements)}")
    print(f"   Constraints Found: {len(spec3.constraints)}")
    print(f"   Success Criteria: {len(spec3.success_criteria)}")

    print("\n✅ Edge case tests completed!")


if __name__ == "__main__":
    test_delegation_builder()
    test_edge_cases()
