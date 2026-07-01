"""
Log Generator Script
Generates sample application logs for testing
"""
import random
import time
from datetime import datetime
import boto3

# Sample log messages
LOG_MESSAGES = {
    'INFO': [
        'User login successful',
        'Application started successfully',
        'Database connection established',
        'Cache cleared successfully',
        'API request processed',
        'File uploaded successfully',
        'Backup completed',
        'Configuration loaded',
        'Session started',
        'Health check passed'
    ],
    'WARNING': [
        'High memory usage detected',
        'Slow database query detected',
        'Disk space running low',
        'API rate limit approaching',
        'Deprecated function called',
        'Connection pool nearly exhausted',
        'Cache miss rate high',
        'Response time above threshold',
        'Memory leak detected',
        'Too many concurrent connections'
    ],
    'ERROR': [
        'Database connection failed',
        'API request timeout',
        'File not found',
        'Permission denied',
        'Invalid user input',
        'Service unavailable',
        'Network error occurred',
        'Authentication failed',
        'Data validation error',
        'External service error'
    ],
    'CRITICAL': [
        'Segmentation fault',
        'Out of memory error',
        'System crash detected',
        'Security breach attempt',
        'Database corruption',
        'Complete service failure',
        'Kernel panic',
        'Critical system error',
        'Data loss detected',
        'Fatal error in core module'
    ]
}

def generate_log():
    """Generate a random log entry"""
    level = random.choices(
        ['INFO', 'INFO', 'INFO', 'WARNING', 'WARNING', 'ERROR', 'ERROR', 'CRITICAL'],
        weights=[40, 40, 40, 15, 15, 8, 8, 4]
    )[0]
    
    message = random.choice(LOG_MESSAGES[level])
    timestamp = datetime.now().isoformat()
    
    return f"{timestamp} [{level}] {message}"

def write_to_file(log_file='application.log', num_logs=100):
    """Write logs to a file"""
    print(f"Generating {num_logs} logs to {log_file}...")
    
    with open(log_file, 'w') as f:
        for _ in range(num_logs):
            log = generate_log()
            f.write(log + '\n')
            time.sleep(0.01)  # Small delay to simulate real logs
    
    print(f"Successfully generated {num_logs} logs")

def stream_logs(log_file='application.log', interval=5):
    """Continuously generate and stream logs"""
    print(f"Streaming logs to {log_file} every {interval} seconds...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            log = generate_log()
            with open(log_file, 'a') as f:
                f.write(log + '\n')
                f.flush()
            print(log)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nLog streaming stopped")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--stream':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        stream_logs(interval=interval)
    else:
        num_logs = int(sys.argv[1]) if len(sys.argv) > 1 else 100
        write_to_file(num_logs=num_logs)
