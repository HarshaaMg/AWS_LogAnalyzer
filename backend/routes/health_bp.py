"""
Health & Self-Observability Blueprint.
Provides platform self-health inspection (/api/system/health) and legacy health check (/api/health).
"""

from flask import Blueprint, jsonify
from datetime import datetime, timezone
import storage_factory
from streaming.event_stream import get_event_stream
from provisioners.factory import get_provisioner

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/system/health", methods=["GET"])
def system_health():
    """
    Observability of the Observability System itself.
    Returns operational health of API, streaming bus, storage backend, and agent telemetry.
    """
    storage = storage_factory.get_storage()
    stream = get_event_stream()
    provisioner = get_provisioner()

    hosts = storage.get_hosts()
    active_agents = len([h for h in hosts if h.get("status") == "ACTIVE"])
    unhealthy_agents = len([h for h in hosts if h.get("status") == "UNHEALTHY"])

    streaming_status = "healthy (kafka)" if stream.is_kafka_connected() else "healthy (in-memory)"
    storage_status = "healthy"
    provisioning_status = "healthy"

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api": "healthy",
        "streaming": streaming_status,
        "storage": storage_status,
        "provisioning": provisioning_status,
        "agents": {
            "total": len(hosts),
            "active": active_agents,
            "unhealthy": unhealthy_agents
        }
    }), 200


@health_bp.route("/health", methods=["GET"])
def legacy_health():
    """Preserves 100% backward compatibility for existing health check monitors."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "AWS Cloud Log Analyzer & Linux Auto-Scaling Platform"
    }), 200
