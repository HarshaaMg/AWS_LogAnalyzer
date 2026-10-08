"""
CloudWatch Logs Sender
Sends logs from application.log to AWS CloudWatch
"""
import boto3
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
cloudwatch_logs = boto3.client(
    'logs',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

LOG_GROUP_NAME = '/aws/cloud-log-analyzer/application'
LOG_STREAM_NAME = 'application-logs'

def create_log_group():
    """Create CloudWatch log group if it doesn't exist"""
    try:
        cloudwatch_logs.create_log_group(logGroupName=LOG_GROUP_NAME)
        print(f"Created log group: {LOG_GROUP_NAME}")
    except cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
        print(f"Log group {LOG_GROUP_NAME} already exists")
    except Exception as e:
        print(f"Error creating log group: {e}")

def create_log_stream():
    """Create CloudWatch log stream if it doesn't exist"""
    try:
        cloudwatch_logs.create_log_stream(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=LOG_STREAM_NAME
        )
        print(f"Created log stream: {LOG_STREAM_NAME}")
    except cloudwatch_logs.exceptions.ResourceAlreadyExistsException:
        print(f"Log stream {LOG_STREAM_NAME} already exists")
    except Exception as e:
        print(f"Error creating log stream: {e}")

def send_logs_to_cloudwatch(log_file='application.log'):
    """Read logs from file and send to CloudWatch"""
    create_log_group()
    create_log_stream()
    
    if not os.path.exists(log_file):
        fallback = os.path.join(os.path.dirname(__file__), '..', 'backend', 'logs', os.path.basename(log_file))
        if os.path.exists(fallback):
            log_file = fallback
        else:
            print(f"Log file {log_file} not found")
            return
    
    print(f"Reading logs from {log_file}...")
    
    with open(log_file, 'r') as f:
        logs = f.readlines()
    
    # CloudWatch accepts batches of log events
    batch_size = 100
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i + batch_size]
        
        log_events = []
        for log in batch:
            log_events.append({
                'timestamp': int(time.time() * 1000),
                'message': log.strip()
            })
        
        try:
            cloudwatch_logs.put_log_events(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=LOG_STREAM_NAME,
                logEvents=log_events
            )
            print(f"Sent batch {i//batch_size + 1} ({len(batch)} logs)")
        except Exception as e:
            print(f"Error sending logs: {e}")
        
        time.sleep(0.1)  # Small delay between batches
    
    print(f"Successfully sent {len(logs)} logs to CloudWatch")

def tail_log_file(log_file='application.log', interval=10):
    """Continuously monitor log file and send new logs to CloudWatch"""
    create_log_group()
    create_log_stream()
    
    print(f"Monitoring {log_file} and sending to CloudWatch every {interval} seconds...")
    print("Press Ctrl+C to stop")
    
    # Get initial file size
    last_size = 0
    if os.path.exists(log_file):
        last_size = os.path.getsize(log_file)
    
    try:
        while True:
            if os.path.exists(log_file):
                current_size = os.path.getsize(log_file)
                
                if current_size > last_size:
                    with open(log_file, 'r') as f:
                        f.seek(last_size)
                        new_logs = f.readlines()
                    
                    if new_logs:
                        log_events = []
                        for log in new_logs:
                            log_events.append({
                                'timestamp': int(time.time() * 1000),
                                'message': log.strip()
                            })
                        
                        try:
                            cloudwatch_logs.put_log_events(
                                logGroupName=LOG_GROUP_NAME,
                                logStreamName=LOG_STREAM_NAME,
                                logEvents=log_events
                            )
                            print(f"Sent {len(log_events)} new logs to CloudWatch")
                        except Exception as e:
                            print(f"Error sending logs: {e}")
                    
                    last_size = current_size
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped monitoring log file")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--tail':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        tail_log_file(interval=interval)
    else:
        log_file = sys.argv[1] if len(sys.argv) > 1 else 'application.log'
        send_logs_to_cloudwatch(log_file=log_file)
