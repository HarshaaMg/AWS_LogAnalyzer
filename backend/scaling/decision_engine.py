"""
Resource Shortage Decision Engine.
Evaluates sustained metrics, enforces safety policies (cooldown, locks, min/max limits, dry-run),
and triggers automated VM provisioning when resource exhaustion is confirmed.
"""

import os
import time
import threading
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import storage_factory
from models.entities import create_incident_entity, create_scaling_event_entity, ScalingAction, IncidentSeverity


class DecisionEngine:
    """Evaluates cluster metrics against safety constraints and decides scaling actions."""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DecisionEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        # Configurable thresholds
        self.cpu_warning = float(os.getenv("CPU_WARNING_THRESHOLD", "75.0"))
        self.cpu_critical = float(os.getenv("CPU_CRITICAL_THRESHOLD", "90.0"))
        self.mem_warning = float(os.getenv("MEM_WARNING_THRESHOLD", "75.0"))
        self.mem_critical = float(os.getenv("MEM_CRITICAL_THRESHOLD", "90.0"))
        self.disk_warning = float(os.getenv("DISK_WARNING_THRESHOLD", "80.0"))
        self.disk_critical = float(os.getenv("DISK_CRITICAL_THRESHOLD", "90.0"))

        # Safety constraints
        self.min_vm_count = int(os.getenv("MIN_VM_COUNT", "1"))
        self.max_vm_count = int(os.getenv("MAX_VM_COUNT", "5"))
        self.cooldown_seconds = int(os.getenv("COOLDOWN_PERIOD", "300"))  # 5 minutes
        self.auto_scaling_enabled = os.getenv("AUTO_SCALING_ENABLED", "true").lower() in ("true", "1")
        self.dry_run_mode = os.getenv("DRY_RUN_MODE", "true").lower() in ("true", "1")

        # State tracking
        self.last_scale_up_time = 0.0
        self.last_scale_down_time = 0.0
        self.scaling_in_progress = False

        self._initialized = True

    def get_scaling_status(self) -> Dict[str, Any]:
        """Returns the current operational status of the scaling engine."""
        storage = storage_factory.get_storage()
        hosts = storage.get_hosts()
        active_count = len([h for h in hosts if h.get("status") == "ACTIVE"])
        provisioning_count = len([h for h in hosts if h.get("status") in ("PROVISIONING", "BOOTING", "CONFIGURING")])

        time_since_last_scale = int(time.time() - self.last_scale_up_time) if self.last_scale_up_time > 0 else 9999
        in_cooldown = time_since_last_scale < self.cooldown_seconds

        return {
            "auto_scaling_enabled": self.auto_scaling_enabled,
            "dry_run_mode": self.dry_run_mode,
            "min_vm_count": self.min_vm_count,
            "max_vm_count": self.max_vm_count,
            "current_vm_count": len(hosts),
            "active_vm_count": active_count,
            "provisioning_vm_count": provisioning_count,
            "scaling_in_progress": self.scaling_in_progress or (provisioning_count > 0),
            "in_cooldown": in_cooldown,
            "cooldown_remaining_seconds": max(0, self.cooldown_seconds - time_since_last_scale) if in_cooldown else 0,
            "last_scale_up": datetime.fromtimestamp(self.last_scale_up_time, tz=timezone.utc).isoformat() if self.last_scale_up_time > 0 else None,
            "last_scale_down": datetime.fromtimestamp(self.last_scale_down_time, tz=timezone.utc).isoformat() if self.last_scale_down_time > 0 else None
        }

    def evaluate_host(self, host_id: str, window_stats: Dict[str, Any]) -> Tuple[ScalingAction, str]:
        """
        Evaluates a host's window statistics and determines whether scale-up is required.
        Returns (ScalingAction, ReasonString).
        """
        with self._lock:
            avg_cpu = window_stats.get("avg_cpu", 0.0)
            avg_mem = window_stats.get("avg_memory", 0.0)
            sustained_cpu = window_stats.get("sustained_high_cpu", False)
            sustained_mem = window_stats.get("sustained_high_memory", False)
            sample_count = window_stats.get("sample_count", 0)

            # Check for resource warning / incidents
            storage = storage_factory.get_storage()

            if avg_cpu >= self.cpu_critical or sustained_cpu:
                incident = create_incident_entity(
                    incident_id=f"inc_cpu_{int(time.time())}_{host_id}",
                    host_id=host_id,
                    incident_type="RESOURCE_HIGH_CPU",
                    severity=IncidentSeverity.CRITICAL.value,
                    threshold=self.cpu_critical,
                    actual_value=avg_cpu,
                    duration="5m",
                    action_taken="SCALE_UP" if self.auto_scaling_enabled else "ALERT_ONLY"
                )
                storage.add_incident(incident)

            if avg_mem >= self.mem_critical or sustained_mem:
                incident = create_incident_entity(
                    incident_id=f"inc_mem_{int(time.time())}_{host_id}",
                    host_id=host_id,
                    incident_type="RESOURCE_HIGH_MEMORY",
                    severity=IncidentSeverity.CRITICAL.value,
                    threshold=self.mem_critical,
                    actual_value=avg_mem,
                    duration="5m",
                    action_taken="SCALE_UP" if self.auto_scaling_enabled else "ALERT_ONLY"
                )
                storage.add_incident(incident)

            # Check if auto-scaling is enabled
            if not self.auto_scaling_enabled:
                return ScalingAction.NONE, "Auto-scaling is disabled"

            # Check if condition is sustained (prevent knee-jerk scale-up on single spike)
            condition_sustained = (sustained_cpu or sustained_mem or (avg_cpu >= self.cpu_critical and sample_count >= 3))
            if not condition_sustained:
                return ScalingAction.NONE, "Condition not sustained (no action taken)"

            # Check if scaling is already in progress
            hosts = storage.get_hosts()
            provisioning_hosts = [h for h in hosts if h.get("status") in ("PROVISIONING", "BOOTING", "CONFIGURING")]
            if self.scaling_in_progress or provisioning_hosts:
                return ScalingAction.NONE, "Scaling already in progress (locked)"

            # Check cooldown period
            now = time.time()
            if (now - self.last_scale_up_time) < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - (now - self.last_scale_up_time))
                return ScalingAction.NONE, f"In cooldown period ({remaining}s remaining)"

            # Check maximum VM limits
            if len(hosts) >= self.max_vm_count:
                return ScalingAction.NONE, f"Maximum VM limit reached ({self.max_vm_count})"

            # Condition satisfied: Scale-Up Triggered
            reason = f"Sustained resource exhaustion detected on {host_id} (CPU: {avg_cpu}%, Mem: {avg_mem}%)"
            return ScalingAction.SCALE_UP, reason

    def mark_scale_up_initiated(self):
        """Sets scaling lock and records timestamp."""
        with self._lock:
            self.scaling_in_progress = True
            self.last_scale_up_time = time.time()

    def mark_scale_up_finished(self):
        """Clears scaling lock."""
        with self._lock:
            self.scaling_in_progress = False

    def mark_scale_down_finished(self):
        with self._lock:
            self.last_scale_down_time = time.time()


_decision_engine = None

def get_decision_engine() -> DecisionEngine:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine
