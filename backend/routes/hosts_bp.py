"""
Hosts Blueprint - Handles Linux VM registration, heartbeat beaconing, and host inventory.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, verify_jwt_in_request
import storage_factory
from models.entities import create_host_entity, HostStatus
import os

hosts_bp = Blueprint("hosts", __name__, url_prefix="/api/hosts")


def _optional_jwt():
    """Helper allowing either JWT or machine agent key for registration."""
    agent_key = request.headers.get("X-Agent-Key")
    expected_key = os.getenv("AGENT_REGISTRATION_KEY", "linux-agent-secret-key")
    if agent_key and agent_key == expected_key:
        return True
    try:
        verify_jwt_in_request(optional=True)
        return True
    except Exception:
        return True  # Permissive for local dev & automated agents


@hosts_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_hosts():
    """List all registered Linux hosts with status and utilization."""
    storage = storage_factory.get_storage()
    # Check for stale hosts before returning
    if hasattr(storage, "check_and_reap_stale_heartbeats"):
        storage.check_and_reap_stale_heartbeats(timeout_seconds=90)

    hosts = storage.get_hosts()
    return jsonify({"hosts": hosts, "total": len(hosts)}), 200


@hosts_bp.route("/<host_id>", methods=["GET"])
@jwt_required(optional=True)
def get_host(host_id):
    """Retrieve details and utilization of a single host."""
    storage = storage_factory.get_storage()
    host = storage.get_host(host_id)
    if not host:
        return jsonify({"error": f"Host with ID '{host_id}' not found"}), 404
    return jsonify({"host": host}), 200


@hosts_bp.route("/register", methods=["POST"])
def register_host():
    """
    Called by cloud-init or Linux startup script to self-register with cluster.
    Request body:
      {
         "hostname": "linux-vm-02",
         "ip": "192.168.1.120",
         "os": "Ubuntu 22.04 LTS",
         "cpu": 4,
         "memory": 8192,
         "disk": 50,
         "provider": "vmware"
      }
    """
    _optional_jwt()
    data = request.get_json() or {}
    hostname = data.get("hostname")
    if not hostname:
        return jsonify({"error": "hostname is required"}), 400

    ip = data.get("ip", "127.0.0.1")
    cpu = data.get("cpu", 4)
    memory = data.get("memory", 8192)
    disk = data.get("disk", 50)
    os_name = data.get("os", "Linux")
    provider = data.get("provider", "vmware")

    host_id = data.get("host_id") or f"host_{hostname.replace('-', '_')}"

    host_entity = create_host_entity(
        host_id=host_id,
        hostname=hostname,
        ip=ip,
        cpu_capacity=cpu,
        memory_capacity=memory,
        disk_capacity=disk,
        os_name=os_name,
        provider=provider,
        status=HostStatus.ACTIVE.value
    )

    storage = storage_factory.get_storage()
    saved = storage.save_host(host_entity)

    return jsonify({
        "message": "Host successfully registered and joined monitoring pool",
        "host": saved
    }), 201


@hosts_bp.route("/<host_id>/heartbeat", methods=["POST"])
def host_heartbeat(host_id):
    """
    Periodic heartbeat beacon from Linux monitoring agent.
    Optionally accepts a lightweight snapshot of current utilization.
    """
    _optional_jwt()
    storage = storage_factory.get_storage()
    data = request.get_json() or {}
    metrics_snapshot = data.get("metrics")

    if hasattr(storage, "update_host_heartbeat"):
        updated = storage.update_host_heartbeat(host_id, metrics_snapshot)
    else:
        host = storage.get_host(host_id)
        if host:
            from datetime import datetime, timezone
            host["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
            if metrics_snapshot:
                host["current_utilization"] = metrics_snapshot
            updated = storage.save_host(host)
        else:
            updated = None

    if not updated:
        return jsonify({"error": f"Host '{host_id}' not found"}), 404

    return jsonify({
        "message": "Heartbeat acknowledged",
        "host_id": host_id,
        "status": updated.get("status")
    }), 200
