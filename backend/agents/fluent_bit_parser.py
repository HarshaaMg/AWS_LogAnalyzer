"""
Fluent Bit Log Parser.
Parses streaming Linux syslog, auth.log, and systemd journal messages.
Identifies authentication anomalies, application crashes, and out-of-memory errors.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone

REGEX_AUTH_FAILURE = re.compile(r"(Failed password|authentication failure|invalid user|sudo:\s+auth failure)", re.IGNORECASE)
REGEX_OOM_CRASH = re.compile(r"(Out of memory:\s+Kill process|invoked oom-killer|Killed process|kernel panic)", re.IGNORECASE)
REGEX_SEGFAULT = re.compile(r"(segfault|segmentation fault|core dumped)", re.IGNORECASE)
REGEX_SERVICE_FAILURE = re.compile(r"(failed to start|service failed|exited with status|dependency failed)", re.IGNORECASE)


class FluentBitLogParser:
    """Classifies Linux system, authentication, and application log lines."""

    @staticmethod
    def parse_log_line(line: str, host_id: str = "linux-vm") -> Dict[str, Any]:
        """Parses a log line and assigns category, severity, and alert triggers."""
        now_iso = datetime.now(timezone.utc).isoformat()
        severity = "INFO"
        category = "SYSTEM"
        alert_needed = False

        if REGEX_OOM_CRASH.search(line):
            severity = "CRITICAL"
            category = "OOM_CRASH"
            alert_needed = True
        elif REGEX_SEGFAULT.search(line):
            severity = "CRITICAL"
            category = "APPLICATION_CRASH"
            alert_needed = True
        elif REGEX_AUTH_FAILURE.search(line):
            severity = "WARNING"
            category = "AUTHENTICATION_ANOMALY"
            alert_needed = True
        elif REGEX_SERVICE_FAILURE.search(line):
            severity = "ERROR"
            category = "SERVICE_FAILURE"
            alert_needed = True
        elif "ERROR" in line.upper():
            severity = "ERROR"
            category = "APPLICATION"
        elif "WARN" in line.upper():
            severity = "WARNING"
            category = "APPLICATION"

        return {
            "log_id": f"log_{datetime.now(timezone.utc).timestamp()}",
            "timestamp": now_iso,
            "host_id": host_id,
            "level": severity,
            "severity": severity,
            "category": category,
            "message": line.strip(),
            "source": f"fluent-bit:{host_id}",
            "alert_needed": alert_needed
        }
