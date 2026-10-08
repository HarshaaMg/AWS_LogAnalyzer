"""
VMProvisioner Abstract Base Class.
Provides a uniform abstraction layer for VM provisioning across VMware and AWS EC2.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class VMProvisioner(ABC):
    """Abstract interface for hypervisors and cloud infrastructure providers."""

    @abstractmethod
    def provision_vm(
        self,
        hostname: str,
        cpu_capacity: int = 4,
        memory_capacity: int = 8192,
        disk_capacity: int = 50,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Creates and boots a new Linux virtual machine, configures networking,
        and registers the monitoring agent with the platform.
        """
        pass

    @abstractmethod
    def deprovision_vm(self, host_id: str) -> bool:
        """
        Gracefully terminates and removes a virtual machine from infrastructure.
        """
        pass

    @abstractmethod
    def get_status(self, host_id: str) -> str:
        """
        Checks operational status from hypervisor/cloud API.
        """
        pass
