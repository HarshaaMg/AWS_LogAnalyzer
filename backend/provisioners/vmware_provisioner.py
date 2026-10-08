"""
Layer 1 - VMware Provisioner.
Implements VMProvisioner for VMware vSphere / Workstation environments.
Features an asynchronous lifecycle orchestrator that simulates/manages VM state transitions:
PROVISIONING -> BOOTING -> CONFIGURING -> HEALTH_CHECK -> ACTIVE.
"""

import os
import time
import random
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from provisioners.base import VMProvisioner
from models.entities import create_host_entity, create_provisioning_entity, HostStatus, get_utc_iso
import storage_factory


class VMwareProvisioner(VMProvisioner):
    """VMware infrastructure provisioner."""

    def __init__(self):
        self.vsphere_host = os.getenv("VMWARE_VSPHERE_HOST")
        self.vsphere_user = os.getenv("VMWARE_VSPHERE_USER")
        self.vsphere_password = os.getenv("VMWARE_VSPHERE_PASSWORD")
        self.datacenter = os.getenv("VMWARE_DATACENTER", "ha-datacenter")
        self.vm_template_name = os.getenv("VMWARE_TEMPLATE_NAME", "ubuntu-22.04-template")

    def provision_vm(
        self,
        hostname: str,
        cpu_capacity: int = 4,
        memory_capacity: int = 8192,
        disk_capacity: int = 50,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Provisions a new Linux VM on VMware.
        If dry_run is True, validates and returns simulated success without modifying state.
        """
        storage = storage_factory.get_storage()
        host_id = f"host_vmware_{random.randint(100, 999)}"
        provisioning_id = f"prov_{int(time.time())}_{random.randint(10, 99)}"

        job = create_provisioning_entity(
            provisioning_id=provisioning_id,
            host_id=host_id,
            hostname=hostname,
            provider="vmware",
            dry_run=dry_run
        )
        storage.save_provisioning_job(job)

        if dry_run:
            job["status"] = "DRY_RUN_COMPLETED"
            job["completed_at"] = get_utc_iso()
            job["steps"].append({"step": "DRY_RUN_EVALUATE", "status": "WOULD_PROVISION", "timestamp": get_utc_iso()})
            storage.save_provisioning_job(job)
            return job

        # Create host in initial PROVISIONING state
        ip_suffix = random.randint(102, 240)
        assigned_ip = f"192.168.1.{ip_suffix}"

        host = create_host_entity(
            host_id=host_id,
            hostname=hostname,
            ip=assigned_ip,
            cpu_capacity=cpu_capacity,
            memory_capacity=memory_capacity,
            disk_capacity=disk_capacity,
            os_name="Ubuntu 22.04 LTS (VMware)",
            provider="vmware",
            status=HostStatus.PROVISIONING.value
        )
        storage.save_host(host)

        # Kick off background asynchronous lifecycle thread
        thread = threading.Thread(
            target=self._run_vmware_lifecycle,
            args=(provisioning_id, host_id, assigned_ip),
            daemon=True
        )
        thread.start()

        return job

    def _run_vmware_lifecycle(self, provisioning_id: str, host_id: str, assigned_ip: str):
        """Asynchronously advances the VM through realistic provisioning stages."""
        storage = storage_factory.get_storage()

        stages = [
            ("CLONE_VM_TEMPLATE", HostStatus.BOOTING.value, 2),
            ("ASSIGN_NETWORK_CONFIG", HostStatus.CONFIGURING.value, 2),
            ("INSTALL_AGENTS", HostStatus.HEALTH_CHECK.value, 3),
            ("VERIFY_METRICS_HEARTBEAT", HostStatus.ACTIVE.value, 2)
        ]

        start_time = time.time()

        for step_name, next_status, delay in stages:
            time.sleep(delay)
            # Update host status
            host = storage.get_host(host_id)
            if host:
                host["status"] = next_status
                if next_status == HostStatus.ACTIVE.value:
                    host["current_utilization"] = {
                        "cpu_pct": round(random.uniform(15.0, 30.0), 1),
                        "memory_pct": round(random.uniform(25.0, 40.0), 1),
                        "disk_pct": 20.0,
                        "load_1m": 0.35,
                        "io_read_mb": 2.5,
                        "io_write_mb": 1.8
                    }
                storage.save_host(host)

            # Update provisioning record
            job = storage.get_provisioning_job(provisioning_id)
            if job:
                job["status"] = next_status
                job["steps"].append({
                    "step": step_name,
                    "status": "COMPLETED",
                    "timestamp": get_utc_iso()
                })
                storage.save_provisioning_job(job)

        # Finalize job
        job = storage.get_provisioning_job(provisioning_id)
        if job:
            job["status"] = HostStatus.ACTIVE.value
            job["completed_at"] = get_utc_iso()
            job["duration_seconds"] = int(time.time() - start_time)
            storage.save_provisioning_job(job)

    def deprovision_vm(self, host_id: str) -> bool:
        """Decommissions a VMware Linux VM."""
        storage = storage_factory.get_storage()
        host = storage.get_host(host_id)
        if not host:
            return False

        host["status"] = HostStatus.TERMINATED.value
        storage.save_host(host)
        return True

    def get_status(self, host_id: str) -> str:
        storage = storage_factory.get_storage()
        host = storage.get_host(host_id)
        return host.get("status", HostStatus.FAILED.value) if host else HostStatus.FAILED.value
