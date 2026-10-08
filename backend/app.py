"""
AWS Cloud Log Analyzer & Real-Time Linux Observability Platform.
Full-stack backend providing log ingestion, severity analysis, Prometheus metric aggregation,
event-driven streaming, and automated multi-cloud VM provisioning (VMware & AWS EC2).
"""

import os
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

# Existing Log Analyzer Modules
from local_log_reader import LocalLogReader
from dummy_log_generator import DummyLogGenerator
from notification_service import NotificationService
from aws_storage_adapter import AWSStorageAdapter
import storage_factory

# New Linux Observability & Auto-Scaling Blueprints
from routes.hosts_bp import hosts_bp
from routes.metrics_bp import metrics_bp, ingest_bp
from routes.scaling_bp import scaling_bp
from routes.health_bp import health_bp

# Streaming & Decision Engines
from streaming.stream_processor import get_stream_processor
from scaling.decision_engine import get_decision_engine, ScalingAction
from scaling.scaling_controller import get_scaling_controller

load_dotenv()

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# File Upload & Directory Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'logs')
LOCAL_STORAGE_DIR = os.path.join(BASE_DIR, 'local_storage')
ALLOWED_EXTENSIONS = {'log', 'txt', 'json'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Storage Mode Configuration
STORAGE_MODE = os.getenv('STORAGE_MODE', 'local').lower()

# Initialize storage adapters based on mode
notification_service = NotificationService()
if STORAGE_MODE == 'aws':
    print("[STORAGE] Using AWS Storage Mode")
    storage_adapter = AWSStorageAdapter()
    log_reader = None
    log_generator = None
else:
    print("[STORAGE] Using Local Storage Mode")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    log_reader = LocalLogReader(log_dir=UPLOAD_FOLDER)
    log_generator = DummyLogGenerator(log_dir=UPLOAD_FOLDER)
    storage_adapter = None

    # Auto-seed sample logs if directory is empty for immediate demonstration
    existing_logs = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(('.log', '.txt', '.json'))]
    if not existing_logs:
        print("[INIT] Seeding initial sample application logs for local testing...")
        log_generator.generate_logs(count=120, filename='application.log')
        log_generator.generate_logs(count=30, filename='system.log')

ALERTS_FILE = os.path.join(LOCAL_STORAGE_DIR, 'alerts.json')
STATS_FILE = os.path.join(LOCAL_STORAGE_DIR, 'stats.json')

if STORAGE_MODE == 'local':
    if not os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'w') as f:
            json.dump([], f)

    if not os.path.exists(STATS_FILE) or not existing_logs:
        # Calculate initial stats from seeded logs
        all_seeded = log_reader.get_all_logs() if log_reader else []
        total_seeded = len(all_seeded)
        err_seeded = len([l for l in all_seeded if l.get('level') == 'ERROR'])
        warn_seeded = len([l for l in all_seeded if l.get('level') == 'WARNING'])
        crit_seeded = len([l for l in all_seeded if l.get('level') == 'CRITICAL'])
        err_msgs = [l.get('message', '') for l in all_seeded if l.get('level') == 'ERROR']
        counts = {}
        for m in err_msgs:
            counts[m] = counts.get(m, 0) + 1
        freq = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

        with open(STATS_FILE, 'w') as f:
            json.dump({
                'stat_id': 'latest',
                'total_logs': total_seeded,
                'total_errors': err_seeded,
                'total_warnings': warn_seeded,
                'critical_count': crit_seeded,
                'most_frequent_errors': [{'message': k, 'count': v} for k, v in freq],
                'error_trends': [err_seeded] * 5,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }, f, indent=2)

    # Ensure the primary demo host is ACTIVE on fresh startup
    try:
        storage = storage_factory.get_storage()
        for h in storage.get_hosts():
            if h.get("host_id") == "host_vmware_01":
                h["status"] = "ACTIVE"
                h["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
                storage.save_host(h)
                break
    except Exception as e:
        pass

# Register Blueprints
app.register_blueprint(hosts_bp)
app.register_blueprint(metrics_bp)
app.register_blueprint(ingest_bp)
app.register_blueprint(scaling_bp)
app.register_blueprint(health_bp)

# Mock user for demo authentication
USERS = {
    'admin': 'admin123'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================================================================
# Original Log Analyzer Endpoints (100% Backward Compatible)
# ==============================================================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    if username in USERS and USERS[username] == password:
        access_token = create_access_token(identity=username)
        return jsonify({
            'access_token': access_token,
            'user': username
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Parse the uploaded file
            reader = log_reader or LocalLogReader(log_dir=app.config['UPLOAD_FOLDER'])
            logs = reader.read_log_file(filename)

            if STORAGE_MODE == 'aws' and storage_adapter:
                for log in logs:
                    storage_adapter.add_log(
                        level=log.get('level', 'INFO'),
                        message=log.get('message', ''),
                        source=f'upload:{filename}'
                    )

            critical_count = 0
            error_count = 0
            for log in logs:
                if log.get('level') == 'CRITICAL':
                    notification_service.create_alert(
                        level='CRITICAL',
                        message=log.get('message', ''),
                        source=f'upload:{filename}'
                    )
                    critical_count += 1
                elif log.get('level') == 'ERROR':
                    error_count += 1

            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'logs_parsed': len(logs),
                'critical_errors': critical_count,
                'errors': error_count
            }), 200
        else:
            return jsonify({'error': 'Invalid file type. Allowed: log, txt, json'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
@jwt_required()
def get_logs():
    try:
        limit = int(request.args.get('limit', 50))
        severity = request.args.get('severity')

        if STORAGE_MODE == 'aws' and storage_adapter:
            logs = storage_adapter.get_logs(limit=limit, severity=severity)
        else:
            reader = log_reader or LocalLogReader(log_dir=app.config['UPLOAD_FOLDER'])
            all_logs = reader.get_all_logs()
            logs = reader.filter_logs(all_logs, severity=severity, limit=limit)

        return jsonify({'logs': logs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['POST'])
@jwt_required(optional=True)
def add_log():
    try:
        data = request.json or {}
        level = data.get('level', 'INFO')
        message = data.get('message', '')
        source = data.get('source', 'manual')

        if STORAGE_MODE == 'aws' and storage_adapter:
            log_entry = storage_adapter.add_log(level, message, source)
        else:
            now_iso = datetime.now(timezone.utc).isoformat()
            log_entry = {
                'log_id': f"log_{datetime.now(timezone.utc).timestamp()}",
                'timestamp': now_iso,
                'level': level,
                'message': message,
                'severity': level,
                'source': source
            }
            os.makedirs('logs', exist_ok=True)
            log_line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {log_entry['level']} {log_entry['message']}"
            filepath = os.path.join('logs', 'manual_logs.log')
            with open(filepath, 'a') as f:
                f.write(log_line + '\n')

        if level in ['CRITICAL', 'ERROR']:
            notification_service.create_alert(
                level=level,
                message=message,
                source=source
            )

        return jsonify({'message': 'Log added successfully', 'log': log_entry}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    try:
        if STORAGE_MODE == 'aws' and storage_adapter:
            alerts = storage_adapter.get_alerts()
        else:
            with open(ALERTS_FILE, 'r') as f:
                alerts = json.load(f)
        return jsonify({'alerts': alerts}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        if STORAGE_MODE == 'aws' and storage_adapter:
            stats = storage_adapter.get_stats()
        else:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
        return jsonify({'stats': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/refresh', methods=['POST'])
@jwt_required()
def refresh_stats():
    try:
        if STORAGE_MODE == 'aws' and storage_adapter:
            stats = storage_adapter.refresh_stats()
        else:
            reader = log_reader or LocalLogReader(log_dir=app.config['UPLOAD_FOLDER'])
            logs = reader.get_all_logs()

            total_logs = len(logs)
            total_errors = len([l for l in logs if l.get('level') == 'ERROR'])
            total_warnings = len([l for l in logs if l.get('level') == 'WARNING'])
            critical_count = len([l for l in logs if l.get('level') == 'CRITICAL'])

            for log in logs:
                if log.get('level') == 'CRITICAL':
                    notification_service.create_alert(
                        level='CRITICAL',
                        message=log.get('message', ''),
                        source='log_analysis'
                    )

            error_messages = [l.get('message', '') for l in logs if l.get('level') == 'ERROR']
            error_counts = {}
            for msg in error_messages:
                error_counts[msg] = error_counts.get(msg, 0) + 1
            most_frequent_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

            error_trends = [total_errors] * 5

            stats = {
                'stat_id': 'latest',
                'total_logs': total_logs,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'critical_count': critical_count,
                'most_frequent_errors': [{'message': k, 'count': v} for k, v in most_frequent_errors],
                'error_trends': error_trends,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)

        return jsonify({'message': 'Stats refreshed', 'stats': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Autonomous Cluster Background Supervisor
# ==============================================================================
def start_background_supervisor():
    """
    Background worker that runs every 10 seconds:
    1. Reaps hosts with missing heartbeats (>90s) -> Marks UNHEALTHY
    2. Evaluates rolling windows against DecisionEngine -> Triggers scale-up on sustained shortage
    """
    def _supervisor_loop():
        time.sleep(5)  # Initial warm-up delay
        while True:
            try:
                storage = storage_factory.get_storage()
                processor = get_stream_processor()
                decision_engine = get_decision_engine()
                controller = get_scaling_controller()

                # 1. Heartbeat Watchdog
                if hasattr(storage, "check_and_reap_stale_heartbeats"):
                    reaped = storage.check_and_reap_stale_heartbeats(timeout_seconds=90)
                    for host_id in reaped:
                        notification_service.create_structured_alert(
                            alert_type="VM_UNHEALTHY",
                            host=host_id,
                            value=0.0,
                            threshold=90.0,
                            duration="90s",
                            severity="CRITICAL",
                            action="EXCLUDE_FROM_POOL"
                        )

                # 2. Continuous Metric Evaluation
                hosts = storage.get_hosts()
                for host in hosts:
                    if host.get("status") == "ACTIVE":
                        host_id = host.get("host_id")
                        stats = processor.get_host_stats(host_id)
                        action, reason = decision_engine.evaluate_host(host_id, stats)
                        if action == ScalingAction.SCALE_UP:
                            print(f"[SCALE-UP] Scale-Up Triggered: {reason}")
                            controller.trigger_scale_up(
                                reason=reason,
                                metrics_snapshot=stats,
                                host_id=host_id
                            )

                # 3. Local Development Live Telemetry Stream (keeps local demo cluster active with live metrics)
                if STORAGE_MODE == 'local' and os.getenv("DEMO_TELEMETRY_ENABLED", "true").lower() in ("true", "1"):
                    from agents.node_exporter_collector import NodeExporterCollector
                    for host in hosts:
                        if host.get("status") in ("ACTIVE", "HEALTH_CHECK"):
                            h_id = host.get("host_id")
                            metric = NodeExporterCollector.generate_simulated_metric(h_id, high_load=False)
                            storage.add_metric(metric)
                            storage.update_host_heartbeat(h_id, {
                                "cpu_pct": metric["cpu"]["percentage"],
                                "memory_pct": metric["memory"]["percentage"],
                                "disk_pct": metric["disk"]["percentage"],
                                "load_1m": metric["load"]["load_1m"],
                                "io_read_mb": metric["disk"]["io_read_mb"],
                                "io_write_mb": metric["disk"]["io_write_mb"]
                            })
                            try:
                                from streaming.event_stream import get_event_stream
                                get_event_stream().publish_metric(metric)
                            except Exception:
                                pass

            except Exception as e:
                print(f"Supervisor error: {e}")

            time.sleep(10)

    thread = threading.Thread(target=_supervisor_loop, daemon=True)
    thread.start()


# Launch background supervisor
start_background_supervisor()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
