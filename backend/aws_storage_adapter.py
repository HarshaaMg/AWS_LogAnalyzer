import boto3
import os
from datetime import datetime
import json

class AWSStorageAdapter:
    """AWS Storage Adapter using DynamoDB and CloudWatch"""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.cloudwatch = boto3.client('logs', region_name=self.region)
        self.sns = boto3.client('sns', region_name=self.region)
        
        # Table names
        self.logs_table = self.dynamodb.Table('CloudLogs')
        self.alerts_table = self.dynamodb.Table('CloudAlerts')
        self.stats_table = self.dynamodb.Table('CloudStats')
        
        # SNS topic
        self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
    
    def get_logs(self, limit=50, severity=None):
        """Get logs from DynamoDB"""
        try:
            if severity:
                response = self.logs_table.query(
                    IndexName='SeverityIndex',
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('severity').eq(severity),
                    Limit=limit
                )
            else:
                response = self.logs_table.scan(Limit=limit)
            
            return response.get('Items', [])
        except Exception as e:
            print(f"Error fetching logs from DynamoDB: {e}")
            return []
    
    def add_log(self, level, message, source='application'):
        """Add log to DynamoDB"""
        try:
            log_entry = {
                'log_id': f"log_{datetime.now().timestamp()}",
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'severity': level,
                'source': source
            }
            
            self.logs_table.put_item(Item=log_entry)
            return log_entry
        except Exception as e:
            print(f"Error adding log to DynamoDB: {e}")
            return None
    
    def get_alerts(self):
        """Get alerts from DynamoDB"""
        try:
            response = self.alerts_table.scan()
            return response.get('Items', [])
        except Exception as e:
            print(f"Error fetching alerts from DynamoDB: {e}")
            return []
    
    def get_stats(self):
        """Get stats from DynamoDB"""
        try:
            response = self.stats_table.get_item(Key={'stat_id': 'latest'})
            return response.get('Item', {
                'stat_id': 'latest',
                'total_logs': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'critical_count': 0,
                'most_frequent_errors': [],
                'error_trends': []
            })
        except Exception as e:
            print(f"Error fetching stats from DynamoDB: {e}")
            return {
                'stat_id': 'latest',
                'total_logs': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'critical_count': 0,
                'most_frequent_errors': [],
                'error_trends': []
            }
    
    def refresh_stats(self):
        """Calculate and store stats from logs"""
        try:
            logs = self.get_logs(limit=1000)
            
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
            
            self.stats_table.put_item(Item=stats)
            return stats
        except Exception as e:
            print(f"Error refreshing stats in DynamoDB: {e}")
            return None
    
    def send_sns_alert(self, subject, message):
        """Send alert via SNS"""
        try:
            if not self.sns_topic_arn:
                print("SNS topic ARN not configured")
                return False
            
            self.sns.publish(
                TopicArn=self.sns_topic_arn,
                Subject=f"[AWS Log Analyzer] {subject}",
                Message=message
            )
            print(f"SNS alert sent: {subject}")
            return True
        except Exception as e:
            print(f"Error sending SNS alert: {e}")
            return False
    
    def create_alert(self, level, message, source='aws'):
        """Create alert in DynamoDB and send SNS notification if critical"""
        try:
            alert = {
                'alert_id': f"alert_{datetime.now().timestamp()}",
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'source': source
            }
            
            self.alerts_table.put_item(Item=alert)
            
            # Send SNS notification for critical alerts
            if level == 'CRITICAL':
                self.send_sns_alert(
                    subject=f"CRITICAL: {message}",
                    message=f"A critical error has been detected:\n\n{message}\n\nTimestamp: {datetime.now().isoformat()}"
                )
            
            return alert
        except Exception as e:
            print(f"Error creating alert in DynamoDB: {e}")
            return None
