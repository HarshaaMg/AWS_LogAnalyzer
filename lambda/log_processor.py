import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

logs_table = dynamodb.Table('CloudLogs')
alerts_table = dynamodb.Table('CloudAlerts')
stats_table = dynamodb.Table('CloudStats')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    AWS Lambda function to process CloudWatch logs
    Triggered by CloudWatch Logs subscription filter
    """
    try:
        # Decode CloudWatch logs data
        cw_data = event['awslogs']['data']
        import base64
        import zlib
        
        compressed_logs = base64.b64decode(cw_data)
        uncompressed_logs = zlib.decompress(compressed_logs, 16 + zlib.MAX_WBITS)
        log_events = json.loads(uncompressed_logs.decode('utf-8'))
        
        processed_count = 0
        critical_alerts = []
        
        for log_event in log_events.get('logEvents', []):
            log_message = log_event['message']
            timestamp = log_event['timestamp']
            
            # Parse log level from message
            log_level = parse_log_level(log_message)
            
            # Store in DynamoDB
            log_entry = {
                'log_id': f"log_{timestamp}_{processed_count}",
                'timestamp': datetime.fromtimestamp(timestamp / 1000).isoformat(),
                'level': log_level,
                'message': log_message,
                'severity': log_level,
                'source': 'cloudwatch',
                'raw_timestamp': timestamp
            }
            
            logs_table.put_item(Item=log_entry)
            processed_count += 1
            
            # Check for critical alerts
            if log_level == 'CRITICAL':
                alert = {
                    'alert_id': f"alert_{timestamp}_{processed_count}",
                    'timestamp': datetime.fromtimestamp(timestamp / 1000).isoformat(),
                    'level': 'CRITICAL',
                    'message': log_message,
                    'status': 'active'
                }
                alerts_table.put_item(Item=alert)
                critical_alerts.append(log_message)
                
                # Send SNS notification
                if SNS_TOPIC_ARN:
                    send_sns_alert(log_message)
        
        # Update statistics
        update_statistics()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {processed_count} logs',
                'critical_alerts': len(critical_alerts)
            })
        }
        
    except Exception as e:
        print(f"Error processing logs: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def parse_log_level(message):
    """Extract log level from message"""
    message_upper = message.upper()
    
    if 'CRITICAL' in message_upper:
        return 'CRITICAL'
    elif 'ERROR' in message_upper:
        return 'ERROR'
    elif 'WARNING' in message_upper:
        return 'WARNING'
    else:
        return 'INFO'

def send_sns_alert(message):
    """Send alert via SNS"""
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='🚨 CRITICAL ALERT - AWS Cloud Log Analyzer',
            Message=f"""CRITICAL ALERT DETECTED

{message}

Timestamp: {datetime.now().isoformat()}

Please investigate immediately."""
        )
    except Exception as e:
        print(f"Error sending SNS alert: {str(e)}")

def update_statistics():
    """Update statistics in DynamoDB"""
    try:
        # Get all logs
        response = logs_table.scan()
        logs = response.get('Items', [])
        
        total_logs = len(logs)
        total_errors = len([l for l in logs if l['level'] == 'ERROR'])
        total_warnings = len([l for l in logs if l['level'] == 'WARNING'])
        critical_count = len([l for l in logs if l['level'] == 'CRITICAL'])
        
        # Calculate most frequent errors
        error_messages = [l['message'] for l in logs if l['level'] == 'ERROR']
        error_counts = {}
        for msg in error_messages:
            error_counts[msg] = error_counts.get(msg, 0) + 1
        most_frequent_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats = {
            'stat_id': 'latest',
            'total_logs': total_logs,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'critical_count': critical_count,
            'most_frequent_errors': [{'message': k, 'count': v} for k, v in most_frequent_errors],
            'error_trends': [],
            'updated_at': datetime.now().isoformat()
        }
        
        stats_table.put_item(Item=stats)
    except Exception as e:
        print(f"Error updating statistics: {str(e)}")
