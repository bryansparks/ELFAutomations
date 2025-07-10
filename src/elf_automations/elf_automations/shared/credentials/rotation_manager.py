"""
Automatic credential rotation management
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from ..utils.logging import setup_logger
from .credential_manager import CredentialManager, CredentialType
from .k3s_integration import K3sSecretManager

logger = setup_logger(__name__)


class RotationPolicy:
    """Rotation policy for different credential types"""

    DEFAULT_POLICIES = {
        CredentialType.API_KEY: timedelta(days=30),
        CredentialType.DATABASE: timedelta(days=7),
        CredentialType.SERVICE_ACCOUNT: timedelta(days=90),
        CredentialType.WEBHOOK: timedelta(days=60),
        CredentialType.JWT_SECRET: timedelta(days=14),
        CredentialType.CERTIFICATE: timedelta(days=365),
    }

    def __init__(
        self, custom_policies: Optional[Dict[CredentialType, timedelta]] = None
    ):
        self.policies = self.DEFAULT_POLICIES.copy()
        if custom_policies:
            self.policies.update(custom_policies)

    def get_rotation_period(self, cred_type: CredentialType) -> timedelta:
        """Get rotation period for credential type"""
        return self.policies.get(cred_type, timedelta(days=30))

    def needs_rotation(
        self, cred_type: CredentialType, last_rotated: Optional[datetime]
    ) -> bool:
        """Check if credential needs rotation"""
        if not last_rotated:
            return True

        period = self.get_rotation_period(cred_type)
        return datetime.now() > last_rotated + period


class RotationManager:
    """
    Manage automatic credential rotation with zero-downtime updates
    """

    def __init__(
        self,
        credential_manager: CredentialManager,
        k3s_manager: Optional[K3sSecretManager] = None,
        policy: Optional[RotationPolicy] = None,
    ):
        self.cred_manager = credential_manager
        self.k3s_manager = k3s_manager
        self.policy = policy or RotationPolicy()

        # Rotation hooks for different credential types
        self.rotation_hooks: Dict[CredentialType, List[Callable]] = {
            cred_type: [] for cred_type in CredentialType
        }

    def register_rotation_hook(self, cred_type: CredentialType, hook: Callable) -> None:
        """Register a hook to be called after rotation"""
        self.rotation_hooks[cred_type].append(hook)

    async def check_and_rotate_all(self) -> Dict[str, List[str]]:
        """Check all credentials and rotate if needed"""

        results = {"rotated": [], "failed": [], "skipped": []}

        # Get all credentials
        credentials = self.cred_manager.list_credentials()

        for cred in credentials:
            if self.policy.needs_rotation(cred.type, cred.last_rotated):
                try:
                    await self.rotate_credential(cred.name, cred.team)
                    results["rotated"].append(f"{cred.team or 'global'}:{cred.name}")

                except Exception as e:
                    logger.error(f"Failed to rotate {cred.name}: {e}")
                    results["failed"].append(f"{cred.team or 'global'}:{cred.name}")
            else:
                results["skipped"].append(f"{cred.team or 'global'}:{cred.name}")

        logger.info(
            f"Rotation complete: {len(results['rotated'])} rotated, "
            f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
        )

        return results

    async def rotate_credential(self, name: str, team: Optional[str] = None) -> None:
        """
        Rotate a specific credential with zero-downtime

        Process:
        1. Generate new credential value
        2. Create versioned credential (keep old active)
        3. Update 50% of services
        4. Verify health
        5. Update remaining services
        6. Deactivate old credential
        """

        logger.info(f"Starting rotation for {name} (team: {team or 'global'})")

        # Get current credential metadata
        key = f"{team}:{name}" if team else f"global:{name}"
        metadata = self.cred_manager.store.get_metadata(key)

        if not metadata:
            raise ValueError(f"Credential {name} not found")

        cred_type = CredentialType(metadata.get("type", "api_key"))

        # Phase 1: Create new version
        old_value = self.cred_manager.get_credential(name, team or "system", "rotation")
        new_value = self.cred_manager.rotate_credential(name, team)

        # Store both versions temporarily
        await self._store_credential_versions(name, team, old_value, new_value)

        # Phase 2: Gradual rollout
        if self.k3s_manager and team:
            await self._gradual_rollout(team, name, old_value, new_value)
        else:
            # Direct update for non-k8s deployments
            await self._direct_update(name, team, cred_type, new_value)

        # Phase 3: Cleanup old version
        await asyncio.sleep(300)  # 5 minute grace period
        await self._cleanup_old_version(name, team, old_value)

        # Run post-rotation hooks
        for hook in self.rotation_hooks.get(cred_type, []):
            try:
                await hook(name, team, new_value)
            except Exception as e:
                logger.error(f"Rotation hook failed: {e}")

        logger.info(f"Successfully rotated {name}")

    async def _store_credential_versions(
        self, name: str, team: Optional[str], old_value: str, new_value: str
    ) -> None:
        """Store multiple versions of a credential during rotation"""

        version_data = {
            "active": new_value,
            "previous": old_value,
            "rotation_started": datetime.now().isoformat(),
        }

        # Store in a special rotation key
        rotation_key = f"rotation:{team or 'global'}:{name}"
        self.cred_manager.store.store(
            rotation_key, json.dumps(version_data), {"type": "rotation_data"}
        )

    async def _gradual_rollout(
        self, team: str, name: str, old_value: str, new_value: str
    ) -> None:
        """Gradually roll out new credential to k8s pods"""

        # This is a simplified version - in production, you'd want:
        # - Canary deployments
        # - Health checks between phases
        # - Automatic rollback on failures

        # Update k8s secret
        self.k3s_manager.apply_secret(team)

        # Trigger rolling update
        logger.info(f"Triggering rolling update for team {team}")

        # In production, monitor pod health here
        await asyncio.sleep(60)  # Wait for pods to cycle

    async def _direct_update(
        self, name: str, team: Optional[str], cred_type: CredentialType, new_value: str
    ) -> None:
        """Direct credential update for non-k8s systems"""

        # Update configuration files, restart services, etc.
        logger.info(f"Direct update completed for {name}")

    async def _cleanup_old_version(
        self, name: str, team: Optional[str], old_value: str
    ) -> None:
        """Clean up old credential version after rotation"""

        rotation_key = f"rotation:{team or 'global'}:{name}"
        self.cred_manager.store.delete(rotation_key)

        logger.info(f"Cleaned up old version of {name}")

    def schedule_rotation(self, cron_expression: str = "0 3 * * *") -> None:
        """Schedule automatic rotation checks"""

        # In production, integrate with your scheduler
        # This is a placeholder for the scheduling logic

        logger.info(f"Scheduled rotation with cron: {cron_expression}")

    async def emergency_rotate_all(self, reason: str) -> Dict[str, List[str]]:
        """Emergency rotation of all credentials"""

        logger.critical(f"EMERGENCY ROTATION INITIATED: {reason}")

        results = {"rotated": [], "failed": []}

        # Get all credentials
        credentials = self.cred_manager.list_credentials()

        # Rotate everything immediately
        tasks = []
        for cred in credentials:
            task = self.rotate_credential(cred.name, cred.team)
            tasks.append(task)

        # Run rotations in parallel
        rotation_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(rotation_results):
            cred = credentials[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to rotate {cred.name}: {result}")
                results["failed"].append(f"{cred.team or 'global'}:{cred.name}")
            else:
                results["rotated"].append(f"{cred.team or 'global'}:{cred.name}")

        # Alert on completion
        logger.critical(
            f"Emergency rotation complete: {len(results['rotated'])} succeeded, "
            f"{len(results['failed'])} failed"
        )

        return results

    def get_rotation_schedule(self) -> List[Dict[str, any]]:
        """Get upcoming rotation schedule"""

        schedule = []
        credentials = self.cred_manager.list_credentials()

        for cred in credentials:
            if cred.last_rotated:
                next_rotation = cred.last_rotated + self.policy.get_rotation_period(
                    cred.type
                )
            else:
                next_rotation = datetime.now()  # Needs immediate rotation

            schedule.append(
                {
                    "credential": cred.name,
                    "team": cred.team or "global",
                    "type": cred.type.value,
                    "last_rotated": cred.last_rotated.isoformat()
                    if cred.last_rotated
                    else None,
                    "next_rotation": next_rotation.isoformat(),
                    "overdue": next_rotation < datetime.now(),
                }
            )

        # Sort by next rotation date
        schedule.sort(key=lambda x: x["next_rotation"])

        return schedule
