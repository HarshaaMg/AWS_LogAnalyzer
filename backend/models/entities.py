"""
Data models and entities for Real-Time Linux Observability and Auto-Scaling Platform.
Supports both Local Storage Mode and AWS DynamoDB Mode.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum


class HostStatus(str, Enum):
    PROVISIONING = "PROVISIONING"
    BOOTING = "BOOTING"
    CONFIGURING = "CONFIGURING"
    HEALTH_CHECK = "HEALTH_CHECK"
    ACTIVE = "ACTIVE"
    UNHEALTHY = "UNHEALTHY"
    FAILED = "FAILED"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class ScalingAction(str, Enum):
    SCALE_UP = "SCALE_UP"
    SCALE_DOWN = "SCALE_DOWN"
    DRAIN = "DRAIN"
    NONE = "NONE"


class IncidentSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ProvisioningProvider(str, Enum):
    VMWARE = "vmware"
    AWS = "aws"
    SIMULATION = "simulation"


def get_utc_iso() -> str:
    """Helper to return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def create_host_entity(
    host_id: str,
    hostname: str,
    ip: str,
    cpu_capacity: int = 4,
    memory_capacity: int = 8192,
    disk_capacity: int = 50,
    os_name: str = "Ubuntu 22.04 LTS",
    provider: str = "vmware",
    status: str = HostStatus.PROVISIONING.value
) -> Dict[str, Any]:
    """Create a standardized host dictionary record."""
    now = get_utc_iso()
    return {
        "host_id": host_id,
        "hostname": hostname,
        "ip": ip,
        "os": os_name,
        "cpu_capacity": int(cpu_capacity),
        "memory_capacity": int(memory_capacity),  # in MB
        "disk_capacity": int(disk_capacity),      # in GB
        "provider": provider,
        "status": status,
        "active_workloads": 0,
        "created_at": now,
        "last_heartbeat": now,
        "current_utilization": {
            "cpu_pct": 0.0,
            "memory_pct": 0.0,
            "disk_pct": 0.0,
            "load_1m": 0.0,
            "io_read_mb": 0.0,
            "io_write_mb": 0.0
        }
    }


def create_metric_entity(
    host_id: str,
    cpu_pct: float,
    user_cpu: float = 0.0,
    system_cpu: float = 0.0,
    idle_cpu: float = 100.0,
    memory_pct: float = 0.0,
    memory_used_mb: float = 0.0,
    memory_total_mb: float = 8192.0,
    disk_pct: float = 0.0,
    disk_used_gb: float = 0.0,
    disk_total_gb: float = 50.0,
    load_1m: float = 0.0,
    load_5m: float = 0.0,
    load_15m: float = 0.0,
    io_read_mb: float = 0.0,
    io_write_mb: float = 0.0,
    app_error_rate: float = 0.0,
    system_errors: int = 0,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized resource metric sample."""
    return {
        "host_id": host_id,
        "timestamp": timestamp or get_utc_iso(),
        "cpu": {
            "percentage": round(float(cpu_pct), 2),
            "user": round(float(user_cpu), 2),
            "system": round(float(system_cpu), 2),
            "idle": round(float(idle_cpu), 2)
        },
        "memory": {
            "percentage": round(float(memory_pct), 2),
            "used_mb": round(float(memory_used_mb), 2),
            "total_mb": round(float(memory_total_mb), 2),
            "available_mb": round(float(memory_total_mb - memory_used_mb), 2)
        },
        "disk": {
            "percentage": round(float(disk_pct), 2),
            "used_gb": round(float(disk_used_gb), 2),
            "total_gb": round(float(disk_total_gb), 2),
            "free_gb": round(float(disk_total_gb - disk_used_gb), 2),
            "io_read_mb": round(float(io_read_mb), 2),
            "io_write_mb": round(float(io_write_mb), 2)
        },
        "load": {
            "load_1m": round(float(load_1m), 2),
            "load_5m": round(float(load_5m), 2),
            "load_15m": round(float(load_15m), 2)
        },
        "errors": {
            "app_error_rate": round(float(app_error_rate), 2),
            "system_errors": int(system_errors)
        }
    }


def create_scaling_event_entity(
    event_id: str,
    action: str,
    reason: str,
    metrics_snapshot: Dict[str, Any],
    host_id: Optional[str] = None,
    provider: str = "vmware",
    status: str = "INITIATED"
) -> Dict[str, Any]:
    """Create a scaling event audit record."""
    return {
        "event_id": event_id,
        "timestamp": get_utc_iso(),
        "host_id": host_id or "cluster",
        "action": action,
        "reason": reason,
        "metrics_snapshot": metrics_snapshot,
        "provider": provider,
        "status": status
    }


def create_incident_entity(
    incident_id: str,
    host_id: str,
    incident_type: str,
    severity: str,
    threshold: float,
    actual_value: float,
    duration: str = "5m",
    action_taken: str = "SCALE_UP",
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create an incident record."""
    now = get_utc_iso()
    return {
        "incident_id": incident_id,
        "host_id": host_id,
        "type": incident_type,
        "severity": severity,
        "threshold": threshold,
        "actual_value": actual_value,
        "duration": duration,
        "action": action_taken,
        "message": message or f"Threshold exceeded for {incident_type}: {actual_value}% >= {threshold}% ({duration})",
        "start_time": now,
        "end_time": None,
        "status": "ACTIVE"
    }


def create_provisioning_entity(
    provisioning_id: str,
    host_id: str,
    hostname: str,
    provider: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Create a provisioning tracking job."""
    now = get_utc_iso()
    return {
        "provisioning_id": provisioning_id,
        "host_id": host_id,
        "hostname": hostname,
        "provider": provider,
        "status": HostStatus.PROVISIONING.value,
        "dry_run": dry_run,
        "started_at": now,
        "completed_at": None,
        "duration_seconds": 0,
        "error": None,
        "steps": [
            {"step": "ALLOCATE_RESOURCE", "status": "COMPLETED", "timestamp": now}
        ]
    }
