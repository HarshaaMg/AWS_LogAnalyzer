"""
Stream Processor & Metric Windowing Engine.
Maintains sliding time-windows for each host to compute rolling averages
and detect sustained resource constraints (differentiating real overload from transient spikes).
"""

import time
import threading
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timezone


class MetricSample:
    __slots__ = ("timestamp", "cpu_pct", "memory_pct", "disk_pct", "load_1m", "app_error_rate")

    def __init__(self, timestamp: float, cpu: float, memory: float, disk: float, load: float, errors: float):
        self.timestamp = timestamp
        self.cpu_pct = cpu
        self.memory_pct = memory
        self.disk_pct = disk
        self.load_1m = load
        self.app_error_rate = errors


class StreamProcessor:
    """Computes rolling statistical windows across streaming Linux metrics."""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, window_seconds: int = 300):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StreamProcessor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, window_seconds: int = 300):
        if getattr(self, "_initialized", False):
            return

        self.window_seconds = window_seconds  # 5 minutes by default
        self._host_windows = defaultdict(lambda: deque(maxlen=60))  # Up to 60 samples per host
        self._listeners = []
        self._initialized = True

    def process_metric(self, metric: Dict[str, Any]):
        """Processes an incoming metric point and updates sliding window statistics."""
        host_id = metric.get("host_id")
        if not host_id:
            return

        sample = MetricSample(
            timestamp=time.time(),
            cpu=metric.get("cpu", {}).get("percentage", 0.0),
            memory=metric.get("memory", {}).get("percentage", 0.0),
            disk=metric.get("disk", {}).get("percentage", 0.0),
            load=metric.get("load", {}).get("load_1m", 0.0),
            errors=metric.get("errors", {}).get("app_error_rate", 0.0)
        )

        with self._lock:
            q = self._host_windows[host_id]
            q.append(sample)
            # Prune samples older than window_seconds
            cutoff = time.time() - self.window_seconds
            while q and q[0].timestamp < cutoff:
                q.popleft()

            stats = self._compute_window_stats(host_id)

        # Notify decision engine listeners if registered
        for listener in self._listeners:
            try:
                listener(host_id, stats)
            except Exception as e:
                print(f"StreamProcessor listener error: {e}")

    def add_listener(self, callback):
        self._listeners.append(callback)

    def _compute_window_stats(self, host_id: str) -> Dict[str, Any]:
        """Calculates rolling statistics over the current window."""
        samples = list(self._host_windows[host_id])
        if not samples:
            return {
                "host_id": host_id,
                "sample_count": 0,
                "duration_seconds": 0,
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
                "avg_disk": 0.0,
                "avg_load": 0.0,
                "sustained_high_cpu": False,
                "sustained_high_memory": False
            }

        count = len(samples)
        duration = int(samples[-1].timestamp - samples[0].timestamp) if count > 1 else 0
        avg_cpu = sum(s.cpu_pct for s in samples) / count
        avg_mem = sum(s.memory_pct for s in samples) / count
        avg_disk = sum(s.disk_pct for s in samples) / count
        avg_load = sum(s.load_1m for s in samples) / count

        # Sustained threshold requires at least 3 samples and average > 90%
        sustained_cpu = count >= 3 and avg_cpu >= 90.0 and all(s.cpu_pct >= 85.0 for s in samples[-3:])
        sustained_mem = count >= 3 and avg_mem >= 90.0 and all(s.memory_pct >= 85.0 for s in samples[-3:])

        return {
            "host_id": host_id,
            "sample_count": count,
            "duration_seconds": duration,
            "avg_cpu": round(avg_cpu, 2),
            "avg_memory": round(avg_mem, 2),
            "avg_disk": round(avg_disk, 2),
            "avg_load": round(avg_load, 2),
            "sustained_high_cpu": sustained_cpu,
            "sustained_high_memory": sustained_mem,
            "latest_cpu": samples[-1].cpu_pct,
            "latest_memory": samples[-1].memory_pct
        }

    def get_host_stats(self, host_id: str) -> Dict[str, Any]:
        with self._lock:
            return self._compute_window_stats(host_id)


_processor_instance = None

def get_stream_processor() -> StreamProcessor:
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = StreamProcessor()
        # Connect to event stream
        from streaming.event_stream import get_event_stream
        get_event_stream().subscribe(_processor_instance.process_metric)
    return _processor_instance
