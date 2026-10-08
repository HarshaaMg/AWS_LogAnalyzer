"""
Streaming Event Bus (Kafka / Redpanda with automatic In-Memory Ring Buffer Fallback).
Guarantees uninterrupted operation even if Kafka broker is unavailable.
"""

import os
import json
import threading
from typing import Dict, Any, Callable, List
from collections import deque


class EventStream:
    """Hybrid Event Streamer supporting Kafka, Redpanda, and In-Memory Queue."""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EventStream, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.metrics_topic = os.getenv("KAFKA_METRICS_TOPIC", "linux-metrics")
        self.logs_topic = os.getenv("KAFKA_LOGS_TOPIC", "linux-logs")

        self.producer = None
        self._memory_metrics_queue = deque(maxlen=5000)
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

        if self.kafka_servers:
            try:
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=self.kafka_servers.split(","),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    request_timeout_ms=3000
                )
                print(f"Connected to Kafka / Redpanda cluster at {self.kafka_servers}")
            except Exception as e:
                print(f"Kafka unavailable ({e}). Falling back to In-Memory Event Bus.")
                self.producer = None
        else:
            print("Kafka not configured. Using In-Memory Event Bus for metrics & logs.")

        self._initialized = True

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a stream consumer listener."""
        with self._lock:
            self._subscribers.append(callback)

    def publish_metric(self, metric: Dict[str, Any]):
        """Publish a metric sample to Kafka or In-Memory buffer."""
        if self.producer:
            try:
                self.producer.send(self.metrics_topic, value=metric)
            except Exception as e:
                print(f"Error publishing to Kafka: {e}")
                self._memory_metrics_queue.append(metric)
        else:
            self._memory_metrics_queue.append(metric)

        # Notify active in-process stream processor subscribers
        for sub in list(self._subscribers):
            try:
                sub(metric)
            except Exception as err:
                print(f"Subscriber error: {err}")

    def get_recent_metrics(self, count: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._memory_metrics_queue)[-count:]

    def is_kafka_connected(self) -> bool:
        return self.producer is not None


_stream_instance = None

def get_event_stream() -> EventStream:
    global _stream_instance
    if _stream_instance is None:
        _stream_instance = EventStream()
    return _stream_instance
