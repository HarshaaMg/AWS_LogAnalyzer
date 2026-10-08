"""
Scaling & Incidents Blueprint.
Provides REST endpoints for auto-scaling management, manual controls,
incident inspection, and provisioning job telemetry.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import storage_factory
from scaling.decision_engine import get_decision_engine
from scaling.scaling_controller import get_scaling_controller
from scaling.workload_scheduler import WorkloadScheduler

scaling_bp = Blueprint("scaling", __name__, url_prefix="/api")


# ------------------------------------------------------------------------------
# Scaling Status & History
# ------------------------------------------------------------------------------
@scaling_bp.route("/scaling/status", methods=["GET"])
@jwt_required(optional=True)
def get_scaling_status():
    """Returns scaling controller state, cooldown, limits, and lock."""
    decision_engine = get_decision_engine()
    status = decision_engine.get_scaling_status()
    return jsonify({"scaling_status": status}), 200


@scaling_bp.route("/scaling/history", methods=["GET"])
@jwt_required(optional=True)
def get_scaling_history():
    """Returns historical log of scaling actions."""
    limit = int(request.args.get("limit", 50))
    storage = storage_factory.get_storage()
    events = storage.get_scaling_events(limit=limit)
    return jsonify({"events": events, "count": len(events)}), 200


@scaling_bp.route("/scaling/scale-up", methods=["POST"])
@jwt_required(optional=True)
def manual_scale_up():
    """Admin-triggered manual scale-up."""
    data = request.get_json() or {}
    reason = data.get("reason", "Manual administrator trigger")
    controller = get_scaling_controller()
    result = controller.trigger_scale_up(
        reason=reason,
        metrics_snapshot={"trigger": "manual_api", "cpu_pct": 95.0, "memory_pct": 92.0}
    )
    return jsonify(result), 200


@scaling_bp.route("/scaling/scale-down", methods=["POST"])
@jwt_required(optional=True)
def manual_scale_down():
    """Admin-triggered manual scale-down."""
    data = request.get_json() or {}
    host_id = data.get("host_id")
    reason = data.get("reason", "Manual administrator decommission")
    controller = get_scaling_controller()
    result = controller.trigger_scale_down(host_id=host_id, reason=reason)
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(result), 200


# ------------------------------------------------------------------------------
# Incidents
# ------------------------------------------------------------------------------
@scaling_bp.route("/incidents", methods=["GET"])
@jwt_required(optional=True)
def get_incidents():
    """Returns list of incidents."""
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    storage = storage_factory.get_storage()
    incidents = storage.get_incidents(status=status, limit=limit)
    return jsonify({"incidents": incidents, "count": len(incidents)}), 200


@scaling_bp.route("/incidents/active", methods=["GET"])
@jwt_required(optional=True)
def get_active_incidents():
    """Returns currently active critical incidents."""
    storage = storage_factory.get_storage()
    incidents = storage.get_incidents(status="ACTIVE")
    return jsonify({"active_incidents": incidents, "count": len(incidents)}), 200


# ------------------------------------------------------------------------------
# Provisioning Jobs
# ------------------------------------------------------------------------------
@scaling_bp.route("/provisioning", methods=["GET"])
@jwt_required(optional=True)
def get_provisioning_jobs():
    """Returns all VM provisioning jobs."""
    limit = int(request.args.get("limit", 20))
    storage = storage_factory.get_storage()
    jobs = storage.get_provisioning_jobs(limit=limit)
    return jsonify({"provisioning_jobs": jobs, "count": len(jobs)}), 200


@scaling_bp.route("/provisioning/<provisioning_id>", methods=["GET"])
@jwt_required(optional=True)
def get_provisioning_job(provisioning_id):
    """Returns details and progress steps of a specific provisioning task."""
    storage = storage_factory.get_storage()
    if hasattr(storage, "get_provisioning_job"):
        job = storage.get_provisioning_job(provisioning_id)
    else:
        jobs = storage.get_provisioning_jobs()
        job = next((j for j in jobs if j.get("provisioning_id") == provisioning_id), None)

    if not job:
        return jsonify({"error": f"Provisioning job '{provisioning_id}' not found"}), 404
    return jsonify({"provisioning_job": job}), 200


# ------------------------------------------------------------------------------
# Workload Allocation
# ------------------------------------------------------------------------------
@scaling_bp.route("/workloads/assign", methods=["POST"])
@jwt_required(optional=True)
def assign_workload():
    """Selects the least-utilized healthy VM and assigns a workload."""
    candidate = WorkloadScheduler.select_host_for_workload()
    if not candidate:
        return jsonify({"error": "No healthy active VM available to accept workload"}), 503

    host_id = candidate.get("host_id")
    WorkloadScheduler.assign_workload(host_id)
    return jsonify({
        "message": "Workload successfully scheduled",
        "assigned_host": candidate
    }), 200


@scaling_bp.route("/workloads/release", methods=["POST"])
@jwt_required(optional=True)
def release_workload():
    """Releases active workload counter on a host."""
    data = request.get_json() or {}
    host_id = data.get("host_id")
    if not host_id:
        return jsonify({"error": "host_id is required"}), 400

    WorkloadScheduler.release_workload(host_id)
    return jsonify({"message": f"Workload released on host '{host_id}'"}), 200
