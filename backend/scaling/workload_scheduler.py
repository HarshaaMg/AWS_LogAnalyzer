"""
Workload Scheduler.
Implements the 'Least-Utilized Healthy VM' workload distribution strategy.
Assigns and tracks workloads across active Linux VMs in the monitoring cluster.
"""

from typing import Dict, Any, List, Optional
import storage_factory
from models.entities import HostStatus


class WorkloadScheduler:
    """Dispatches tasks to the healthiest, least-utilized Linux VM."""

    @staticmethod
    def select_host_for_workload() -> Optional[Dict[str, Any]]:
        """
        Evaluates all registered hosts and selects the candidate with:
        1. Status == ACTIVE
        2. Lowest CPU and Memory utilization score
        3. Lowest active workload count
        """
        storage = storage_factory.get_storage()
        hosts = storage.get_hosts()

        active_hosts = [h for h in hosts if h.get("status") == HostStatus.ACTIVE.value]
        if not active_hosts:
            return None

        def host_score(h: Dict[str, Any]) -> float:
            util = h.get("current_utilization", {})
            cpu = util.get("cpu_pct", 0.0)
            mem = util.get("memory_pct", 0.0)
            workloads = h.get("active_workloads", 0)
            # Weighted score: CPU (50%) + Memory (30%) + active workloads (20%)
            return (cpu * 0.5) + (mem * 0.3) + (workloads * 10.0)

        best_host = min(active_hosts, key=host_score)
        return best_host

    @staticmethod
    def assign_workload(host_id: str) -> bool:
        """Increments active workload counter on the selected host."""
        storage = storage_factory.get_storage()
        host = storage.get_host(host_id)
        if not host or host.get("status") != HostStatus.ACTIVE.value:
            return False

        host["active_workloads"] = host.get("active_workloads", 0) + 1
        storage.save_host(host)
        return True

    @staticmethod
    def release_workload(host_id: str) -> bool:
        """Decrements active workload counter when task completes."""
        storage = storage_factory.get_storage()
        host = storage.get_host(host_id)
        if not host:
            return False

        host["active_workloads"] = max(0, host.get("active_workloads", 0) - 1)
        storage.save_host(host)
        return True
