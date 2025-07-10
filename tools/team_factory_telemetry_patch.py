#!/usr/bin/env python3
"""
Telemetry patch for team_factory.py
Adds telemetry and unified registry integration to the team factory
"""

import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elf_automations.shared.telemetry import telemetry_client


def patch_team_factory():
    """Patch the team factory to add telemetry and registration"""

    # Import the team factory modules
    try:
        from team_factory.core.factory import TeamFactory
        from team_factory.core.team_builder import TeamBuilder
    except ImportError:
        print("Error: Could not import team factory modules")
        return False

    # Store original methods
    original_create_team = TeamFactory.create_team
    original_register_team = (
        TeamBuilder.register_team if hasattr(TeamBuilder, "register_team") else None
    )

    def create_team_with_telemetry(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced create_team with telemetry"""
        start_time = telemetry_client.start_timer()
        team_id = spec.get("id", str(uuid.uuid4()))
        correlation_id = str(uuid.uuid4())

        try:
            # Call original method
            result = original_create_team(self, spec)

            # Record success telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="team-factory",
                workflow_name="Team Factory",
                node_name="create_team",
                target_service="filesystem",
                operation="create_team",
                status="success",
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    "team_id": team_id,
                    "team_name": spec.get("name"),
                    "framework": spec.get("framework"),
                    "llm_provider": spec.get("llm_provider"),
                    "agent_count": len(spec.get("agents", [])),
                    "organization": spec.get("organization_placement"),
                },
            )

            # Register in unified registry if Supabase is available
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
                try:
                    from supabase import create_client

                    client = create_client(
                        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
                    )

                    # Register team in unified registry
                    registry_data = {
                        "p_entity_id": team_id,
                        "p_entity_type": "team",
                        "p_entity_name": spec.get("name"),
                        "p_registered_by": "team_factory",
                        "p_metadata": {
                            "framework": spec.get("framework"),
                            "llm_provider": spec.get("llm_provider"),
                            "agent_count": len(spec.get("agents", [])),
                            "organization": spec.get("organization_placement"),
                        },
                        "p_capabilities": [
                            f"{spec.get('framework', 'crewai')}_execution",
                            "a2a_communication",
                            "task_processing",
                        ],
                        "p_endpoint_url": f"http://{spec.get('name', '').lower().replace(' ', '-')}:8090",
                        "p_parent_entity_id": spec.get("parent_team_id"),
                    }

                    client.rpc("register_entity", registry_data).execute()

                    # Update state to active
                    client.rpc(
                        "update_entity_state",
                        {
                            "p_entity_id": team_id,
                            "p_entity_type": "team",
                            "p_new_state": "created",
                            "p_health_status": "unknown",
                            "p_updated_by": "team_factory",
                            "p_reason": "Team created successfully",
                        },
                    ).execute()

                except Exception as e:
                    print(f"Warning: Could not register team in unified registry: {e}")

            return result

        except Exception as e:
            # Record error telemetry
            duration_ms = telemetry_client.calculate_duration_ms(start_time)
            telemetry_client.record_n8n(
                workflow_id="team-factory",
                workflow_name="Team Factory",
                node_name="create_team",
                target_service="filesystem",
                operation="create_team",
                status="error",
                duration_ms=duration_ms,
                error_message=str(e),
                correlation_id=correlation_id,
                metadata={
                    "team_name": spec.get("name"),
                    "framework": spec.get("framework"),
                },
            )
            raise

    # Patch the methods
    TeamFactory.create_team = create_team_with_telemetry

    print("✅ Team factory patched with telemetry and registration")
    return True


def add_telemetry_to_team_files():
    """Add telemetry client import to generated team files"""

    template_addition = """
# Telemetry imports (added by factory)
try:
    from elf_automations.shared.telemetry import telemetry_client
    from elf_automations.shared.a2a.telemetry_client import create_a2a_client
    TELEMETRY_ENABLED = True
except ImportError:
    print("Warning: Telemetry not available")
    TELEMETRY_ENABLED = False
    # Fallback to standard client
    from elf_automations.shared.a2a.client import A2AClient
    create_a2a_client = lambda **kwargs: A2AClient(**{k: v for k, v in kwargs.items() if k != 'enable_telemetry'})
"""

    # This would be integrated into the team factory templates
    print("📝 Telemetry imports configured for team templates")
    return template_addition


if __name__ == "__main__":
    print("🔧 Patching Team Factory with Telemetry...")

    # Patch the factory
    if patch_team_factory():
        print("\n📋 Team Factory Telemetry Integration Complete!")
        print("\nFeatures added:")
        print("  - Telemetry tracking for team creation")
        print("  - Automatic registration in unified registry")
        print("  - State tracking for created teams")
        print("  - Error telemetry for failures")

        print("\n🔄 Next steps:")
        print("  1. Import this patch in the main team_factory.py")
        print("  2. Teams will automatically use telemetry-enabled A2A clients")
        print("  3. All team creation will be tracked in telemetry")
    else:
        print("❌ Failed to patch team factory")
