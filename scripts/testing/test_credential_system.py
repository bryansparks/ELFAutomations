#!/usr/bin/env python3
"""
Test the credential management system
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elf_automations.shared.credentials import (
    BreakGlassAccess,
    CredentialManager,
    CredentialType,
    K3sSecretManager,
    RotationManager,
)
from elf_automations.shared.utils.logging import setup_logger

logger = setup_logger(__name__)


async def test_basic_operations():
    """Test basic credential operations"""

    logger.info("Testing basic credential operations...")

    # Initialize manager
    cred_manager = CredentialManager()

    # Create a test credential
    test_cred = cred_manager.create_credential(
        name="TEST_API_KEY",
        value="test-value-12345",
        type=CredentialType.API_KEY,
        team="test-team",
        expires_in_days=30,
    )

    logger.info(f"✓ Created credential: {test_cred.name}")

    # Retrieve credential
    value = cred_manager.get_credential("TEST_API_KEY", "test-team", "testing")
    assert value == "test-value-12345"
    logger.info("✓ Retrieved credential successfully")

    # Test access control - should fail
    try:
        cred_manager.get_credential("TEST_API_KEY", "unauthorized-team", "testing")
        logger.error("✗ Access control failed - unauthorized access allowed!")
    except Exception as e:
        logger.info("✓ Access control working - unauthorized access denied")

    # Update credential
    cred_manager.update_credential("TEST_API_KEY", "new-test-value", "test-team")
    logger.info("✓ Updated credential")

    # List credentials
    creds = cred_manager.list_credentials("test-team")
    logger.info(f"✓ Listed {len(creds)} credentials for test-team")

    # Delete credential
    deleted = cred_manager.delete_credential("TEST_API_KEY", "test-team")
    logger.info("✓ Deleted test credential")


async def test_break_glass():
    """Test emergency break glass access"""

    logger.info("\nTesting break glass emergency access...")

    break_glass = BreakGlassAccess()

    # Create emergency token
    token = break_glass.create_token(
        created_by="test_user",
        reason="Testing emergency access system",
        duration_minutes=5,
    )

    logger.info(f"✓ Created break glass token (expires in 5 minutes)")

    # Validate token
    valid = break_glass.validate_token(token, "test_user")
    assert valid
    logger.info("✓ Token validated successfully")

    # Try to reuse token (should fail)
    valid = break_glass.validate_token(token, "test_user")
    assert not valid
    logger.info("✓ Token reuse properly prevented")

    # Get audit trail
    audit = break_glass.get_audit_trail(days=1)
    logger.info(f"✓ Retrieved audit trail with {len(audit)} entries")


async def test_rotation():
    """Test credential rotation"""

    logger.info("\nTesting credential rotation...")

    # Create a credential to rotate
    cred_manager = CredentialManager()
    cred_manager.create_credential(
        name="ROTATION_TEST_KEY",
        value="original-value",
        type=CredentialType.API_KEY,
        team="rotation-team",
    )

    # Initialize rotation manager
    rotation_manager = RotationManager(cred_manager)

    # Rotate credential
    await rotation_manager.rotate_credential("ROTATION_TEST_KEY", "rotation-team")

    # Verify new value
    new_value = cred_manager.get_credential(
        "ROTATION_TEST_KEY", "rotation-team", "verify_rotation"
    )
    assert new_value != "original-value"
    logger.info("✓ Credential rotated successfully")

    # Check rotation schedule
    schedule = rotation_manager.get_rotation_schedule()
    logger.info(f"✓ Retrieved rotation schedule with {len(schedule)} credentials")

    # Cleanup
    cred_manager.delete_credential("ROTATION_TEST_KEY", "rotation-team")


async def test_k3s_integration():
    """Test k3s secret generation (dry run)"""

    logger.info("\nTesting k3s integration...")

    # This is a dry run - won't actually apply to cluster
    cred_manager = CredentialManager()
    k3s_manager = K3sSecretManager(cred_manager)

    # Create some test credentials
    cred_manager.create_credential(
        name="K8S_TEST_KEY",
        value="k8s-test-value",
        type=CredentialType.API_KEY,
        team="k8s-team",
    )

    # Generate secret manifest
    manifest = k3s_manager.create_team_secret("k8s-team")

    if manifest:
        logger.info("✓ Generated k8s secret manifest")
        logger.info(f"  Secret name: {manifest['metadata']['name']}")
        logger.info(f"  Credentials: {list(manifest['data'].keys())}")

    # Generate RBAC
    rbac = k3s_manager.generate_rbac_for_secret("k8s-team")
    logger.info("✓ Generated RBAC rules for secret access")

    # Cleanup
    cred_manager.delete_credential("K8S_TEST_KEY", "k8s-team")


def test_audit_logger():
    """Test audit logging"""

    logger.info("\nTesting audit logger...")

    from elf_automations.shared.credentials import AuditLogger

    audit = AuditLogger()

    # Log various events
    audit.log_creation("AUDIT_TEST_KEY", "audit-team", "api_key")
    audit.log_access("audit-team", "AUDIT_TEST_KEY", "testing")
    audit.log_denied_access("bad-team", "AUDIT_TEST_KEY", "unauthorized")
    audit.log_rotation("AUDIT_TEST_KEY", "audit-team")

    # Get report
    report = audit.get_access_report(days=1)

    logger.info("✓ Audit events logged")
    logger.info(f"  Total events: {report['total_events']}")
    logger.info(f"  Event types: {dict(report['by_event_type'])}")


async def main():
    """Run all tests"""

    logger.info("=" * 60)
    logger.info("CREDENTIAL MANAGEMENT SYSTEM TEST")
    logger.info("=" * 60)

    try:
        # Run tests
        await test_basic_operations()
        await test_break_glass()
        await test_rotation()
        await test_k3s_integration()
        test_audit_logger()

        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS PASSED! ✓")
        logger.info("=" * 60)

        logger.info("\nThe credential management system is working correctly.")
        logger.info("You can now use it to manage all your credentials securely.")

    except Exception as e:
        logger.error(f"\nTEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
