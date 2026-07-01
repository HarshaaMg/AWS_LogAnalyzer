from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from local_log_reader import LocalLogReader
from dummy_log_generator import DummyLogGenerator
from notification_service import NotificationService
from aws_storage_adapter import AWSStorageAdapter

load_dotenv()

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# File Upload Configuration
UPLOAD_FOLDER = 'logs'
ALLOWED_EXTENSIONS = {'log', 'txt', 'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Storage Mode Configuration
STORAGE_MODE = os.getenv('STORAGE_MODE', 'local').lower()

# Initialize storage adapters based on mode
if STORAGE_MODE == 'aws':
    print("🔷 Using AWS Storage Mode")
    storage_adapter = AWSStorageAdapter()
    notification_service = NotificationService()
else:
    print("💾 Using Local Storage Mode")
    log_reader = LocalLogReader(log_dir='logs')
    log_generator = DummyLogGenerator(log_dir='logs')
    notification_service = NotificationService()
    storage_adapter = None

# Local storage files (only used in local mode)
LOCAL_STORAGE_DIR = 'local_storage'
if STORAGE_MODE == 'local' and not os.path.exists(LOCAL_STORAGE_DIR):
    os.makedirs(LOCAL_STORAGE_DIR)

ALERTS_FILE = os.path.join(LOCAL_STORAGE_DIR, 'alerts.json')
STATS_FILE = os.path.join(LOCAL_STORAGE_DIR, 'stats.json')

# Initialize local storage files
if STORAGE_MODE == 'local':
    if not os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'w') as f:
            json.dump([], f)
    
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w') as f:
            json.dump({
                'stat_id': 'latest',
                'total_logs': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'critical_count': 0,
                'most_frequent_errors': [],
                'error_trends': [],
                'updated_at': datetime.now().isoformat()
            }, f)

# Mock user for demo (in production, use real database)
USERS = {
    'admin': 'admin123'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
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
            
            # Ensure upload directory exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Parse the uploaded file
            logs = log_reader.read_log_file(filename)
            
            # If in AWS mode, also upload to DynamoDB
            if STORAGE_MODE == 'aws':
                for log in logs:
                    storage_adapter.add_log(
                        level=log.get('level', 'INFO'),
                        message=log.get('message', ''),
                        source=f'upload:{filename}'
                    )
            
            # Create alerts for critical errors
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
        
        if STORAGE_MODE == 'aws':
            logs = storage_adapter.get_logs(limit=limit, severity=severity)
        else:
            all_logs = log_reader.get_all_logs()
            logs = log_reader.filter_logs(all_logs, severity=severity, limit=limit)
        
        return jsonify({'logs': logs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['POST'])
@jwt_required()
def add_log():
    try:
        data = request.json
        level = data.get('level', 'INFO')
        message = data.get('message')
        source = data.get('source', 'manual')
        
        if STORAGE_MODE == 'aws':
            log_entry = storage_adapter.add_log(level, message, source)
        else:
            log_entry = {
                'log_id': f"log_{datetime.now().timestamp()}",
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'severity': level,
                'source': source
            }
            # Append to local log file
            log_line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {log_entry['level']} {log_entry['message']}"
            filepath = os.path.join('logs', 'manual_logs.log')
            with open(filepath, 'a') as f:
                f.write(log_line + '\n')
        
        # Create alert if critical or error
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
        if STORAGE_MODE == 'aws':
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
        if STORAGE_MODE == 'aws':
            stats = storage_adapter.get_stats()
        else:
            with open(STATS_FILE, 'r') as f:
                stats = json.load(f)
        return jsonify({'stats': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'AWS Cloud Log Analyzer'
    }), 200

@app.route('/api/stats/refresh', methods=['POST'])
@jwt_required()
def refresh_stats():
    try:
        if STORAGE_MODE == 'aws':
            stats = storage_adapter.refresh_stats()
        else:
            # Read logs from local files
            logs = log_reader.get_all_logs()
            
            total_logs = len(logs)
            total_errors = len([l for l in logs if l['level'] == 'ERROR'])
            total_warnings = len([l for l in logs if l['level'] == 'WARNING'])
            critical_count = len([l for l in logs if l['level'] == 'CRITICAL'])
            
            # Create alerts for critical logs
            for log in logs:
                if log['level'] == 'CRITICAL':
                    notification_service.create_alert(
                        level='CRITICAL',
                        message=log['message'],
                        source='log_analysis'
                    )
            
            # Calculate most frequent errors
            error_messages = [l['message'] for l in logs if l['level'] == 'ERROR']
            error_counts = {}
            for msg in error_messages:
                error_counts[msg] = error_counts.get(msg, 0) + 1
            most_frequent_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Calculate error trends (last 5 time buckets)
            error_trends = []
            for i in range(5):
                bucket_logs = [l for l in logs if l['level'] == 'ERROR']
                error_trends.append(len(bucket_logs))
            
            stats = {
                'stat_id': 'latest',
                'total_logs': total_logs,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'critical_count': critical_count,
                'most_frequent_errors': [{'message': k, 'count': v} for k, v in most_frequent_errors],
                'error_trends': error_trends,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)
        
        return jsonify({'message': 'Stats refreshed', 'stats': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
