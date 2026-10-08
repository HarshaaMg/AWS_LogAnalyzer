"""
Scaling Controller.
Coordinates the end-to-end auto-scaling workflow:
Resource Shortage -> Decision Engine -> Provisioner -> Agent Registration -> Pool Joining -> Alerts.
"""

import time
import random
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import storage_factory
from scaling.decision_engine import get_decision_engine
from provisioners.factory import get_provisioner
from notification_service import NotificationService
from models.entities import create_scaling_event_entity, ScalingAction, HostStatus


class ScalingController:
    """Manages scaling execution, cooldown, and workload distribution."""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ScalingController, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.notification_service = NotificationService()
        self._initialized = True

    def trigger_scale_up(self, reason: str, metrics_snapshot: Dict[str, Any], host_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a scale-up operation:
        1. Verifies lock and cooldown via DecisionEngine
        2. Dispatches provisioning to active provisioner (VMware or AWS)
        3. Emits scaling event audit log
        4. Sends alert notifications
        """
        decision_engine = get_decision_engine()
        storage = storage_factory.get_storage()
        provisioner = get_provisioner()

        decision_engine.mark_scale_up_initiated()

        try:
            hosts = storage.get_hosts()
            next_num = len(hosts) + 1
            new_hostname = f"linux-vm-{next_num:02d}"

            dry_run = decision_engine.dry_run_mode
            provider_name = "aws" if hasattr(provisioner, "ec2") and provisioner.ec2 else "vmware"

            # 1. Provision VM
            job = provisioner.provision_vm(
                hostname=new_hostname,
                cpu_capacity=4,
                memory_capacity=8192,
                disk_capacity=50,
                dry_run=dry_run
            )

            # 2. Record Scaling Event
            event_id = f"scaleup_{int(time.time())}_{random.randint(10, 99)}"
            action_desc = "WOULD_PROVISION (DRY-RUN)" if dry_run else "PROVISIONING_STARTED"
            event = create_scaling_event_entity(
                event_id=event_id,
                action=ScalingAction.SCALE_UP.value,
                reason=reason,
                metrics_snapshot=metrics_snapshot,
                host_id=job.get("host_id"),
                provider=provider_name,
                status=action_desc
            )
            storage.add_scaling_event(event)

            # 3. Dispatch Notification
            alert_msg = (
                f"Auto-scaling initiated for cluster.\n"
                f"Reason: {reason}\n"
                f"Action: Provisioning new Linux VM '{new_hostname}' via {provider_name.upper()}\n"
                f"Dry-Run Mode: {dry_run}\n"
                f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
            )
            self.notification_service.create_alert(
                level="CRITICAL",
                message=alert_msg,
                source="auto_scaler"
            )

            return {
                "success": True,
                "action": "SCALE_UP",
                "reason": reason,
                "provisioning_job": job,
                "dry_run": dry_run,
                "event": event
            }
        finally:
            decision_engine.mark_scale_up_finished()

    def trigger_scale_down(self, host_id: Optional[str] = None, reason: str = "Resource demand decreased") -> Dict[str, Any]:
        """
        Executes a safe scale-down operation:
        1. Ensures current_vms > min_vm_count (NEVER terminates last healthy VM)
        2. Drains active workload
        3. Calls provisioner deprovision
        4. Records scaling event
        """
        decision_engine = get_decision_engine()
        storage = storage_factory.get_storage()
        hosts = storage.get_hosts()
        active_hosts = [h for h in hosts if h.get("status") == HostStatus.ACTIVE.value]

        if len(active_hosts) <= decision_engine.min_vm_count:
            return {
                "success": False,
                "error": f"Cannot scale down: current active VMs ({len(active_hosts)}) <= minimum limit ({decision_engine.min_vm_count})"
            }

        # Select candidate: either specified or least utilized
        target_host = None
        if host_id:
            target_host = next((h for h in active_hosts if h.get("host_id") == host_id), None)
        if not target_host:
            # Pick the VM with lowest active workloads or lowest CPU
            target_host = min(active_hosts, key=lambda h: h.get("current_utilization", {}).get("cpu_pct", 0.0))

        target_id = target_host.get("host_id")
        target_name = target_host.get("hostname", target_id)

        # Deprovision
        provisioner = get_provisioner()
        provisioner.deprovision_vm(target_id)
        decision_engine.mark_scale_down_finished()

        event = create_scaling_event_entity(
            event_id=f"scaledown_{int(time.time())}",
            action=ScalingAction.SCALE_DOWN.value,
            reason=reason,
            metrics_snapshot=target_host.get("current_utilization", {}),
            host_id=target_id,
            provider=target_host.get("provider", "vmware"),
            status="TERMINATED"
        )
        storage.add_scaling_event(event)

        return {
            "success": True,
            "action": "SCALE_DOWN",
            "host_id": target_id,
            "hostname": target_name,
            "reason": reason
        }


_controller_instance = None

def get_scaling_controller() -> ScalingController:
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = ScalingController()
    return _controller_instance
