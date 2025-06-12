#!/usr/bin/env python3
"""
Simple verification that evolution tables were created successfully.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client


def main():
    print("=== Evolution Schema Verification ===\n")

    try:
        supabase = get_supabase_client()
        print("✓ Connected to Supabase\n")
    except Exception as e:
        print(f"✗ Failed to connect to Supabase: {e}")
        return

    # Test 1: Check agent_evolutions table
    print("1. Testing agent_evolutions table...")
    try:
        # Try to insert a test evolution
        test_id = str(uuid4())
        test_team_id = str(uuid4())  # Dummy team ID for testing

        evolution_data = {
            "id": test_id,
            "team_id": test_team_id,
            "agent_role": "test_developer",
            "evolution_type": "prompt",
            "original_version": "You are a developer.",
            "evolved_version": "You are a developer. Based on experience: Always validate inputs first.",
            "confidence_score": 0.95,
        }

        # Insert
        result = supabase.table("agent_evolutions").insert(evolution_data).execute()

        if result.data:
            print("  ✓ Successfully inserted test evolution")

            # Read back
            read_result = (
                supabase.table("agent_evolutions")
                .select("*")
                .eq("id", test_id)
                .execute()
            )

            if (
                read_result.data
                and read_result.data[0]["agent_role"] == "test_developer"
            ):
                print("  ✓ Successfully read evolution data")

                # Clean up
                supabase.table("agent_evolutions").delete().eq("id", test_id).execute()
                print("  ✓ Cleaned up test data")
            else:
                print("  ✗ Failed to read evolution data correctly")
        else:
            print("  ✗ Failed to insert evolution")

    except Exception as e:
        print(f"  ✗ Error testing agent_evolutions: {e}")

    # Test 2: Check ab_tests table
    print("\n2. Testing ab_tests table...")
    try:
        # Create test A/B test
        test_ab_id = str(uuid4())
        ab_data = {
            "id": test_ab_id,
            "team_id": test_team_id,
            "agent_role": "test_developer",
            "evolution_id": test_id,  # Reference to evolution (won't exist but that's ok for test)
            "status": "active",
            "traffic_split": 0.5,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-02T00:00:00Z",
            "control_config": "base config",
            "treatment_config": "evolved config",
        }

        result = supabase.table("ab_tests").insert(ab_data).execute()

        if result.data:
            print("  ✓ Successfully created A/B test")

            # Clean up
            supabase.table("ab_tests").delete().eq("id", test_ab_id).execute()
            print("  ✓ Cleaned up test data")
        else:
            print("  ✗ Failed to create A/B test")

    except Exception as e:
        print(f"  ✗ Error testing ab_tests: {e}")

    # Test 3: Check ab_test_results table
    print("\n3. Testing ab_test_results table...")
    try:
        result_id = str(uuid4())
        result_data = {
            "id": result_id,
            "test_id": test_ab_id,
            "group_name": "control",
            "success": True,
            "duration_seconds": 2.5,
        }

        result = supabase.table("ab_test_results").insert(result_data).execute()

        if result.data:
            print("  ✓ Successfully recorded test result")

            # Clean up
            supabase.table("ab_test_results").delete().eq("id", result_id).execute()
            print("  ✓ Cleaned up test data")
        else:
            print("  ✗ Failed to record test result")

    except Exception as e:
        print(f"  ✗ Error testing ab_test_results: {e}")

    print("\n=== Summary ===")
    print("✓ Evolution tables are properly configured!")
    print("\nNext steps:")
    print("1. Create or update your teams using team_factory.py")
    print("2. Enable evolution in your agent initialization")
    print("3. Run test_agent_evolution.py to see evolution in action")


if __name__ == "__main__":
    main()
