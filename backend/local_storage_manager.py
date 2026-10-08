"""
Local file storage manager for Linux hosts, metrics, scaling events, incidents, and provisioning.
Provides thread-safe atomic reading/writing to backend/local_storage/ JSON files.
"""

import os
import json
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from models.entities import create_host_entity, HostStatus


DEFAULT_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_storage")


class LocalStorageManager:
    """Manages JSON file persistence for local development and VMware environments."""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, storage_dir: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LocalStorageManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_dir: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        self.storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)

        self.hosts_file = os.path.join(self.storage_dir, "hosts.json")
        self.metrics_file = os.path.join(self.storage_dir, "resource_metrics.json")
        self.events_file = os.path.join(self.storage_dir, "scaling_events.json")
        self.incidents_file = os.path.join(self.storage_dir, "incidents.json")
        self.provisioning_file = os.path.join(self.storage_dir, "provisioning.json")

        self._ensure_files()
        self._seed_default_host_if_empty()
        self._initialized = True

    def _ensure_files(self):
        """Initializes empty JSON files if they don't already exist."""
        for path in [
            self.hosts_file,
            self.metrics_file,
            self.events_file,
            self.incidents_file,
            self.provisioning_file,
        ]:
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump([], f, indent=2)

    def _read_json(self, path: str) -> List[Dict[str, Any]]:
        with self._lock:
            try:
                if not os.path.exists(path):
                    return []
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading {path}: {e}")
                return []

    def _write_json(self, path: str, data: Any):
        with self._lock:
            try:
                temp_path = f"{path}.tmp"
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2)
                os.replace(temp_path, path)
            except Exception as e:
                print(f"Error writing {path}: {e}")

    def _seed_default_host_if_empty(self):
        """Ensures at least one primary Linux VM exists in the cluster on first run."""
        hosts = self._read_json(self.hosts_file)
        if not hosts:
            primary_host = create_host_entity(
                host_id="host_vmware_01",
                hostname="linux-vm-01",
                ip="192.168.1.101",
                cpu_capacity=4,
                memory_capacity=8192,
                disk_capacity=60,
                os_name="Ubuntu 22.04 LTS",
                provider="vmware",
                status=HostStatus.ACTIVE.value
            )
            primary_host["current_utilization"] = {
                "cpu_pct": 34.5,
                "memory_pct": 48.2,
                "disk_pct": 52.0,
                "load_1m": 1.15,
                "io_read_mb": 12.4,
                "io_write_mb": 8.6
            }
            hosts.append(primary_host)
            self._write_json(self.hosts_file, hosts)

    # --------------------------------------------------------------------------
    # Hosts Management
    # --------------------------------------------------------------------------
    def get_hosts(self) -> List[Dict[str, Any]]:
        return self._read_json(self.hosts_file)

    def get_host(self, host_id: str) -> Optional[Dict[str, Any]]:
        hosts = self.get_hosts()
        for h in hosts:
            if h.get("host_id") == host_id:
                return h
        return None

    def save_host(self, host: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            hosts = self.get_hosts()
            existing_idx = next((i for i, h in enumerate(hosts) if h.get("host_id") == host.get("host_id")), None)
            if existing_idx is not None:
                hosts[existing_idx] = host
            else:
                hosts.append(host)
            self._write_json(self.hosts_file, hosts)
            return host

    def update_host_heartbeat(self, host_id: str, current_metrics: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            hosts = self.get_hosts()
            target = next((h for h in hosts if h.get("host_id") == host_id), None)
            if not target:
                return None
            target["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            if target.get("status") in (HostStatus.UNHEALTHY.value, HostStatus.HEALTH_CHECK.value):
                target["status"] = HostStatus.ACTIVE.value
            if current_metrics:
                target["current_utilization"] = current_metrics
            self._write_json(self.hosts_file, hosts)
            return target

    def check_and_reap_stale_heartbeats(self, timeout_seconds: int = 90) -> List[str]:
        """Marks hosts as UNHEALTHY if no heartbeat received within timeout_seconds."""
        with self._lock:
            hosts = self.get_hosts()
            reaped_ids = []
            now = datetime.now(timezone.utc)

            for h in hosts:
                if h.get("status") in (HostStatus.ACTIVE.value, HostStatus.CONFIGURING.value):
                    last_hb_str = h.get("last_heartbeat")
                    if last_hb_str:
                        try:
                            last_hb = datetime.fromisoformat(last_hb_str)
                            if (now - last_hb).total_seconds() > timeout_seconds:
                                h["status"] = HostStatus.UNHEALTHY.value
                                reaped_ids.append(h.get("host_id"))
                        except Exception:
                            pass

            if reaped_ids:
                self._write_json(self.hosts_file, hosts)
            return reaped_ids

    # --------------------------------------------------------------------------
    # Resource Metrics
    # --------------------------------------------------------------------------
    def add_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            metrics = self._read_json(self.metrics_file)
            metrics.append(metric)
            # Retain last 2,000 metrics locally to prevent unbounded growth
            if len(metrics) > 2000:
                metrics = metrics[-2000:]
            self._write_json(self.metrics_file, metrics)

            host_id = metric.get("host_id")
            if host_id:
                host = self.get_host(host_id)
                if host:
                    cpu_val = metric.get("cpu", {}).get("percentage") if isinstance(metric.get("cpu"), dict) else metric.get("cpu_pct", 0.0)
                    mem_val = metric.get("memory", {}).get("percentage") if isinstance(metric.get("memory"), dict) else metric.get("memory_pct", 0.0)
                    disk_val = metric.get("disk", {}).get("percentage") if isinstance(metric.get("disk"), dict) else metric.get("disk_pct", 0.0)
                    load_val = metric.get("load", {}).get("load_1m") if isinstance(metric.get("load"), dict) else metric.get("load_1m", 0.0)
                    io_read = metric.get("disk", {}).get("io_read_mb") if isinstance(metric.get("disk"), dict) else metric.get("io_read_mb", 0.0)
                    io_write = metric.get("disk", {}).get("io_write_mb") if isinstance(metric.get("disk"), dict) else metric.get("io_write_mb", 0.0)

                    host["current_utilization"] = {
                        "cpu_pct": cpu_val,
                        "memory_pct": mem_val,
                        "disk_pct": disk_val,
                        "load_1m": load_val,
                        "io_read_mb": io_read,
                        "io_write_mb": io_write
                    }
                    self.save_host(host)

            return metric

    def get_metrics(self, host_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        metrics = self._read_json(self.metrics_file)
        if host_id:
            filtered = [m for m in metrics if m.get("host_id") == host_id]
        else:
            filtered = metrics
        return filtered[-limit:]

    # --------------------------------------------------------------------------
    # Scaling Events
    # --------------------------------------------------------------------------
    def add_scaling_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            events = self._read_json(self.events_file)
            events.append(event)
            self._write_json(self.events_file, events)
            return event

    def get_scaling_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = self._read_json(self.events_file)
        return sorted(events, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    # --------------------------------------------------------------------------
    # Incidents
    # --------------------------------------------------------------------------
    def add_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            incidents = self._read_json(self.incidents_file)
            incidents.append(incident)
            self._write_json(self.incidents_file, incidents)
            return incident

    def get_incidents(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        incidents = self._read_json(self.incidents_file)
        if status:
            filtered = [inc for inc in incidents if inc.get("status") == status]
        else:
            filtered = incidents
        return sorted(filtered, key=lambda x: x.get("start_time", ""), reverse=True)[:limit]

    def resolve_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            incidents = self._read_json(self.incidents_file)
            target = next((inc for inc in incidents if inc.get("incident_id") == incident_id), None)
            if target:
                target["status"] = "RESOLVED"
                target["end_time"] = datetime.now(timezone.utc).isoformat()
                self._write_json(self.incidents_file, incidents)
                return target
            return None

    # --------------------------------------------------------------------------
    # Provisioning Jobs
    # --------------------------------------------------------------------------
    def save_provisioning_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            jobs = self._read_json(self.provisioning_file)
            idx = next((i for i, j in enumerate(jobs) if j.get("provisioning_id") == job.get("provisioning_id")), None)
            if idx is not None:
                jobs[idx] = job
            else:
                jobs.append(job)
            self._write_json(self.provisioning_file, jobs)
            return job

    def get_provisioning_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        jobs = self._read_json(self.provisioning_file)
        return sorted(jobs, key=lambda x: x.get("started_at", ""), reverse=True)[:limit]

    def get_provisioning_job(self, provisioning_id: str) -> Optional[Dict[str, Any]]:
        jobs = self._read_json(self.provisioning_file)
        for j in jobs:
            if j.get("provisioning_id") == provisioning_id:
                return j
        return None
