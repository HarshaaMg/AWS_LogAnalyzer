"""
Metrics Blueprint - Resource utilization querying and metric ingestion.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import storage_factory
from models.entities import create_metric_entity

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/resources")


@metrics_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def get_cluster_resources():
    """Returns cluster-wide aggregated utilization and capacity statistics."""
    storage = storage_factory.get_storage()
    hosts = storage.get_hosts()

    total_hosts = len(hosts)
    active_hosts = [h for h in hosts if h.get("status") == "ACTIVE"]
    active_count = len(active_hosts)
    unhealthy_count = len([h for h in hosts if h.get("status") == "UNHEALTHY"])
    provisioning_count = len([h for h in hosts if h.get("status") in ("PROVISIONING", "BOOTING", "CONFIGURING", "HEALTH_CHECK")])

    if active_count > 0:
        avg_cpu = sum(h.get("current_utilization", {}).get("cpu_pct", 0.0) for h in active_hosts) / active_count
        avg_mem = sum(h.get("current_utilization", {}).get("memory_pct", 0.0) for h in active_hosts) / active_count
        avg_disk = sum(h.get("current_utilization", {}).get("disk_pct", 0.0) for h in active_hosts) / active_count
        avg_load = sum(h.get("current_utilization", {}).get("load_1m", 0.0) for h in active_hosts) / active_count
    else:
        avg_cpu, avg_mem, avg_disk, avg_load = 0.0, 0.0, 0.0, 0.0

    total_cpu_cores = sum(h.get("cpu_capacity", 0) for h in hosts)
    total_mem_mb = sum(h.get("memory_capacity", 0) for h in hosts)
    total_disk_gb = sum(h.get("disk_capacity", 0) for h in hosts)

    return jsonify({
        "cluster_summary": {
            "total_hosts": total_hosts,
            "active_hosts": active_count,
            "unhealthy_hosts": unhealthy_count,
            "provisioning_hosts": provisioning_count,
            "average_cpu_pct": round(avg_cpu, 1),
            "average_memory_pct": round(avg_mem, 1),
            "average_disk_pct": round(avg_disk, 1),
            "average_load_1m": round(avg_load, 2),
            "total_cpu_cores": total_cpu_cores,
            "total_memory_gb": round(total_mem_mb / 1024, 1),
            "total_disk_gb": total_disk_gb
        }
    }), 200


@metrics_bp.route("/<metric_type>", methods=["GET"])
@jwt_required(optional=True)
def get_resource_metric_history(metric_type):
    """
    Returns time-series history for charts: 'cpu', 'memory', 'disk', 'load', or 'io'.
    Query params: ?host_id=<id>&limit=50
    """
    valid_types = ("cpu", "memory", "disk", "load", "io")
    if metric_type not in valid_types:
        return jsonify({"error": f"Invalid metric type. Must be one of: {', '.join(valid_types)}"}), 400

    host_id = request.args.get("host_id")
    limit = int(request.args.get("limit", 50))

    storage = storage_factory.get_storage()
    metrics = storage.get_metrics(host_id=host_id, limit=limit)

    series = []
    for m in metrics:
        ts = m.get("timestamp", "")
        if metric_type == "cpu":
            val = m.get("cpu", {}).get("percentage", 0.0)
        elif metric_type == "memory":
            val = m.get("memory", {}).get("percentage", 0.0)
        elif metric_type == "disk":
            val = m.get("disk", {}).get("percentage", 0.0)
        elif metric_type == "load":
            val = m.get("load", {}).get("load_1m", 0.0)
        elif metric_type == "io":
            val = round(m.get("disk", {}).get("io_read_mb", 0.0) + m.get("disk", {}).get("io_write_mb", 0.0), 2)
        else:
            val = 0.0

        series.append({"timestamp": ts, "value": val, "host_id": m.get("host_id")})

    return jsonify({
        "metric": metric_type,
        "count": len(series),
        "data": series
    }), 200


# Endpoint mounted under /api/metrics/ingest for agent data intake
ingest_bp = Blueprint("metrics_ingest", __name__, url_prefix="/api/metrics")

@ingest_bp.route("/ingest", methods=["POST"])
def ingest_metrics():
    """
    Ingests metric telemetry from Node Exporter collectors, Fluent Bit, or VM agents.
    """
    data = request.get_json() or {}
    host_id = data.get("host_id")
    if not host_id:
        return jsonify({"error": "host_id is required"}), 400

    cpu_data = data.get("cpu", {}) if isinstance(data.get("cpu"), dict) else {}
    mem_data = data.get("memory", {}) if isinstance(data.get("memory"), dict) else {}
    disk_data = data.get("disk", {}) if isinstance(data.get("disk"), dict) else {}
    load_data = data.get("load", {}) if isinstance(data.get("load"), dict) else {}
    err_data = data.get("errors", {}) if isinstance(data.get("errors"), dict) else {}

    entity = create_metric_entity(
        host_id=host_id,
        cpu_pct=data.get("cpu_pct", cpu_data.get("percentage", 0.0)),
        user_cpu=data.get("user_cpu", cpu_data.get("user", 0.0)),
        system_cpu=data.get("system_cpu", cpu_data.get("system", 0.0)),
        idle_cpu=data.get("idle_cpu", cpu_data.get("idle", 100.0)),
        memory_pct=data.get("memory_pct", mem_data.get("percentage", 0.0)),
        memory_used_mb=data.get("memory_used_mb", mem_data.get("used_mb", 0.0)),
        memory_total_mb=data.get("memory_total_mb", mem_data.get("total_mb", 8192.0)),
        disk_pct=data.get("disk_pct", disk_data.get("percentage", 0.0)),
        disk_used_gb=data.get("disk_used_gb", disk_data.get("used_gb", 0.0)),
        disk_total_gb=data.get("disk_total_gb", disk_data.get("total_gb", 50.0)),
        load_1m=data.get("load_1m", load_data.get("load_1m", 0.0)),
        load_5m=data.get("load_5m", load_data.get("load_5m", 0.0)),
        load_15m=data.get("load_15m", load_data.get("load_15m", 0.0)),
        io_read_mb=data.get("io_read_mb", disk_data.get("io_read_mb", 0.0)),
        io_write_mb=data.get("io_write_mb", disk_data.get("io_write_mb", 0.0)),
        app_error_rate=data.get("app_error_rate", err_data.get("app_error_rate", 0.0)),
        system_errors=data.get("system_errors", err_data.get("system_errors", 0)),
        timestamp=data.get("timestamp")
    )

    storage = storage_factory.get_storage()
    saved = storage.add_metric(entity)

    # Route metric through StreamProcessor if active
    try:
        from streaming.event_stream import get_event_stream
        get_event_stream().publish_metric(saved)
    except Exception as e:
        # Don't fail ingestion if streaming layer is offline
        pass

    return jsonify({"message": "Metric ingested successfully", "host_id": host_id}), 201
