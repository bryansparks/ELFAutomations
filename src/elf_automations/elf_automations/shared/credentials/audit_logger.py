"""
Comprehensive audit logging for credential operations
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class AuditEvent:
    """Audit event types"""

    CREATED = "credential_created"
    ACCESSED = "credential_accessed"
    UPDATED = "credential_updated"
    DELETED = "credential_deleted"
    ROTATED = "credential_rotated"
    DENIED = "access_denied"
    EXPIRED = "access_expired"
    BREAK_GLASS = "break_glass_used"


class AuditLogger:
    """
    Comprehensive audit logging for all credential operations
    Provides compliance-ready audit trail
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".elf_automations" / "audit"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Separate logs by date for easier rotation
        self.current_date = datetime.now().date()
        self.log_file = self._get_log_file()

    def _get_log_file(self) -> Path:
        """Get current log file path"""
        return self.storage_path / f"audit_{self.current_date.isoformat()}.jsonl"

    def _rotate_if_needed(self) -> None:
        """Rotate log file if date changed"""
        if datetime.now().date() != self.current_date:
            self.current_date = datetime.now().date()
            self.log_file = self._get_log_file()

    def _log_event(self, event: Dict[str, Any]) -> None:
        """Log an audit event"""
        self._rotate_if_needed()

        # Add timestamp and ID
        event["timestamp"] = datetime.now().isoformat()
        event["event_id"] = f"{event['timestamp']}_{event['event']}"

        # Write as JSON line
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Also log to standard logger
        logger.info(
            f"Audit: {event['event']} - {event.get('team', 'N/A')} - {event.get('credential', 'N/A')}"
        )

    def log_creation(self, credential: str, team: Optional[str], type: str) -> None:
        """Log credential creation"""
        self._log_event(
            {
                "event": AuditEvent.CREATED,
                "credential": credential,
                "team": team or "global",
                "type": type,
                "success": True,
            }
        )

    def log_access(self, team: str, credential: str, purpose: str) -> None:
        """Log successful credential access"""
        self._log_event(
            {
                "event": AuditEvent.ACCESSED,
                "team": team,
                "credential": credential,
                "purpose": purpose,
                "success": True,
            }
        )

    def log_denied_access(self, team: str, credential: str, purpose: str) -> None:
        """Log denied credential access"""
        self._log_event(
            {
                "event": AuditEvent.DENIED,
                "team": team,
                "credential": credential,
                "purpose": purpose,
                "success": False,
                "severity": "warning",
            }
        )

        # Alert on multiple denied attempts
        if self._count_recent_denials(team, credential) >= 3:
            self._send_security_alert(
                f"Multiple access denials: Team {team} attempting to access {credential}"
            )

    def log_expired_access(self, team: str, credential: str) -> None:
        """Log access attempt to expired credential"""
        self._log_event(
            {
                "event": AuditEvent.EXPIRED,
                "team": team,
                "credential": credential,
                "success": False,
                "severity": "warning",
            }
        )

    def log_update(
        self, credential: str, team: Optional[str], updated_by: Optional[str]
    ) -> None:
        """Log credential update"""
        self._log_event(
            {
                "event": AuditEvent.UPDATED,
                "credential": credential,
                "team": team or "global",
                "updated_by": updated_by or "system",
                "success": True,
            }
        )

    def log_deletion(
        self, credential: str, team: Optional[str], deleted_by: Optional[str]
    ) -> None:
        """Log credential deletion"""
        self._log_event(
            {
                "event": AuditEvent.DELETED,
                "credential": credential,
                "team": team or "global",
                "deleted_by": deleted_by or "system",
                "success": True,
                "severity": "info",
            }
        )

    def log_rotation(self, credential: str, team: Optional[str]) -> None:
        """Log credential rotation"""
        self._log_event(
            {
                "event": AuditEvent.ROTATED,
                "credential": credential,
                "team": team or "global",
                "success": True,
            }
        )

    def log_break_glass(self, used_by: str, reason: str) -> None:
        """Log break glass access"""
        self._log_event(
            {
                "event": AuditEvent.BREAK_GLASS,
                "used_by": used_by,
                "reason": reason,
                "success": True,
                "severity": "critical",
            }
        )

    def _count_recent_denials(
        self, team: str, credential: str, minutes: int = 5
    ) -> int:
        """Count recent access denials"""
        count = 0
        cutoff = datetime.now() - timedelta(minutes=minutes)

        # Read recent events
        events = self.get_events(minutes=minutes)

        for event in events:
            if (
                event.get("event") == AuditEvent.DENIED
                and event.get("team") == team
                and event.get("credential") == credential
            ):
                count += 1

        return count

    def get_events(
        self,
        days: Optional[int] = None,
        minutes: Optional[int] = None,
        event_type: Optional[str] = None,
        team: Optional[str] = None,
    ) -> List[Dict]:
        """Get audit events with filters"""
        events = []

        # Determine time cutoff
        if minutes:
            cutoff = datetime.now() - timedelta(minutes=minutes)
        elif days:
            cutoff = datetime.now() - timedelta(days=days)
        else:
            cutoff = None

        # Read log files
        log_files = sorted(self.storage_path.glob("audit_*.jsonl"), reverse=True)

        for log_file in log_files:
            # Skip old files if cutoff specified
            if cutoff:
                file_date = datetime.fromisoformat(log_file.stem.replace("audit_", ""))
                if file_date.date() < cutoff.date():
                    break

            # Read events from file
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        event = json.loads(line.strip())

                        # Apply filters
                        if (
                            cutoff
                            and datetime.fromisoformat(event["timestamp"]) < cutoff
                        ):
                            continue

                        if event_type and event["event"] != event_type:
                            continue

                        if team and event.get("team") != team:
                            continue

                        events.append(event)

            except Exception as e:
                logger.error(f"Failed to read audit log {log_file}: {e}")

        return sorted(events, key=lambda x: x["timestamp"], reverse=True)

    def get_access_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive access report"""
        events = self.get_events(days=days)

        report = {
            "period": f"Last {days} days",
            "total_events": len(events),
            "by_event_type": defaultdict(int),
            "by_team": defaultdict(int),
            "by_credential": defaultdict(int),
            "denied_access": [],
            "break_glass_usage": [],
            "anomalies": [],
        }

        # Analyze events
        for event in events:
            event_type = event["event"]
            report["by_event_type"][event_type] += 1

            if "team" in event:
                report["by_team"][event["team"]] += 1

            if "credential" in event:
                report["by_credential"][event["credential"]] += 1

            if event_type == AuditEvent.DENIED:
                report["denied_access"].append(
                    {
                        "timestamp": event["timestamp"],
                        "team": event["team"],
                        "credential": event["credential"],
                    }
                )

            if event_type == AuditEvent.BREAK_GLASS:
                report["break_glass_usage"].append(
                    {
                        "timestamp": event["timestamp"],
                        "used_by": event["used_by"],
                        "reason": event["reason"],
                    }
                )

        # Detect anomalies
        report["anomalies"] = self._detect_anomalies(events)

        return report

    def _detect_anomalies(self, events: List[Dict]) -> List[Dict]:
        """Detect suspicious patterns in audit events"""
        anomalies = []

        # Check for unusual access patterns
        access_by_team_hour = defaultdict(lambda: defaultdict(int))

        for event in events:
            if event["event"] == AuditEvent.ACCESSED:
                hour = datetime.fromisoformat(event["timestamp"]).hour
                team = event["team"]
                access_by_team_hour[team][hour] += 1

        # Flag teams accessing credentials at unusual hours
        for team, hours in access_by_team_hour.items():
            for hour, count in hours.items():
                if 0 <= hour < 6 or 22 <= hour <= 23:  # Late night access
                    if count > 5:  # More than 5 accesses in an hour
                        anomalies.append(
                            {
                                "type": "unusual_hour_access",
                                "team": team,
                                "hour": hour,
                                "count": count,
                                "severity": "medium",
                            }
                        )

        return anomalies

    def _send_security_alert(self, message: str) -> None:
        """Send security alert"""
        alert_file = self.storage_path / "security_alerts.log"
        with open(alert_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")

        logger.warning(f"SECURITY ALERT: {message}")

    def export_for_compliance(
        self, start_date: datetime, end_date: datetime, output_path: Path
    ) -> None:
        """Export audit logs for compliance reporting"""
        events = []

        # Collect events in date range
        current = start_date.date()
        while current <= end_date.date():
            log_file = self.storage_path / f"audit_{current.isoformat()}.jsonl"

            if log_file.exists():
                with open(log_file, "r") as f:
                    for line in f:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event["timestamp"])

                        if start_date <= event_time <= end_date:
                            events.append(event)

            current += timedelta(days=1)

        # Write compliance report
        report = {
            "report_generated": datetime.now().isoformat(),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_events": len(events),
            "events": sorted(events, key=lambda x: x["timestamp"]),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported {len(events)} audit events for compliance")
