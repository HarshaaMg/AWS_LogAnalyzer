import boto3
import os
from datetime import datetime, timezone
import json
from decimal import Decimal
from typing import List, Dict, Any, Optional

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

class AWSStorageAdapter:
    """AWS Storage Adapter using DynamoDB, CloudWatch, and SNS.
    Supports both original log analytics and new Linux VM Observability entities.
    """

    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.cloudwatch = boto3.client('logs', region_name=self.region)
        self.sns = boto3.client('sns', region_name=self.region)

        # Original Table names
        self.logs_table = self.dynamodb.Table(os.getenv('LOGS_TABLE', 'CloudLogs'))
        self.alerts_table = self.dynamodb.Table(os.getenv('ALERTS_TABLE', 'CloudAlerts'))
        self.stats_table = self.dynamodb.Table(os.getenv('STATS_TABLE', 'CloudStats'))

        # Linux Observability & Auto-Scaling Table names
        self.hosts_table = self.dynamodb.Table(os.getenv('HOSTS_TABLE', 'CloudHosts'))
        self.metrics_table = self.dynamodb.Table(os.getenv('METRICS_TABLE', 'CloudResourceMetrics'))
        self.events_table = self.dynamodb.Table(os.getenv('EVENTS_TABLE', 'CloudScalingEvents'))
        self.incidents_table = self.dynamodb.Table(os.getenv('INCIDENTS_TABLE', 'CloudIncidents'))
        self.provisioning_table = self.dynamodb.Table(os.getenv('PROVISIONING_TABLE', 'CloudProvisioning'))

        # SNS topic
        self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN')

    # --------------------------------------------------------------------------
    # Original Log Analyzer Methods (Preserved 100% Backward Compatibility)
    # --------------------------------------------------------------------------
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
                'log_id': f"log_{datetime.now(timezone.utc).timestamp()}",
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
            total_errors = len([l for l in logs if l.get('level') == 'ERROR'])
            total_warnings = len([l for l in logs if l.get('level') == 'WARNING'])
            critical_count = len([l for l in logs if l.get('level') == 'CRITICAL'])

            error_messages = [l.get('message', '') for l in logs if l.get('level') == 'ERROR']
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
                'updated_at': datetime.now(timezone.utc).isoformat()
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
                Subject=f"[AWS Log Analyzer] {subject}"[:100],
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
                'alert_id': f"alert_{datetime.now(timezone.utc).timestamp()}",
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'level': level,
                'message': message,
                'source': source
            }

            self.alerts_table.put_item(Item=alert)

            if level == 'CRITICAL':
                self.send_sns_alert(
                    subject=f"CRITICAL: {message}",
                    message=f"A critical error has been detected:\n\n{message}\n\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
                )

            return alert
        except Exception as e:
            print(f"Error creating alert in DynamoDB: {e}")
            return None

    # --------------------------------------------------------------------------
    # Linux Hosts & Telemetry (AWS Mode Additions)
    # --------------------------------------------------------------------------
    def get_hosts(self) -> List[Dict[str, Any]]:
        try:
            res = self.hosts_table.scan()
            return res.get('Items', [])
        except Exception as e:
            print(f"Error fetching hosts from DynamoDB: {e}")
            return []

    def get_host(self, host_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.hosts_table.get_item(Key={'host_id': host_id})
            return res.get('Item')
        except Exception as e:
            print(f"Error getting host {host_id} from DynamoDB: {e}")
            return None

    def save_host(self, host: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Convert floats to Decimal for DynamoDB compatibility
            item = json.loads(json.dumps(host), parse_float=Decimal)
            self.hosts_table.put_item(Item=item)
            return host
        except Exception as e:
            print(f"Error saving host to DynamoDB: {e}")
            return host

    def add_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item = json.loads(json.dumps(metric), parse_float=Decimal)
            self.metrics_table.put_item(Item=item)
            return metric
        except Exception as e:
            print(f"Error adding metric to DynamoDB: {e}")
            return metric

    def get_metrics(self, host_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            if host_id:
                res = self.metrics_table.query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key('host_id').eq(host_id),
                    ScanIndexForward=False,
                    Limit=limit
                )
            else:
                res = self.metrics_table.scan(Limit=limit)
            return res.get('Items', [])
        except Exception as e:
            print(f"Error getting metrics from DynamoDB: {e}")
            return []

    def add_scaling_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item = json.loads(json.dumps(event), parse_float=Decimal)
            self.events_table.put_item(Item=item)
            return event
        except Exception as e:
            print(f"Error adding scaling event to DynamoDB: {e}")
            return event

    def get_scaling_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            res = self.events_table.scan(Limit=limit)
            items = res.get('Items', [])
            return sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            print(f"Error getting scaling events from DynamoDB: {e}")
            return []

    def add_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item = json.loads(json.dumps(incident), parse_float=Decimal)
            self.incidents_table.put_item(Item=item)
            return incident
        except Exception as e:
            print(f"Error adding incident to DynamoDB: {e}")
            return incident

    def get_incidents(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            res = self.incidents_table.scan(Limit=limit)
            items = res.get('Items', [])
            if status:
                items = [i for i in items if i.get('status') == status]
            return sorted(items, key=lambda x: x.get('start_time', ''), reverse=True)
        except Exception as e:
            print(f"Error getting incidents from DynamoDB: {e}")
            return []

    def save_provisioning_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        try:
            item = json.loads(json.dumps(job), parse_float=Decimal)
            self.provisioning_table.put_item(Item=item)
            return job
        except Exception as e:
            print(f"Error saving provisioning job to DynamoDB: {e}")
            return job

    def get_provisioning_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            res = self.provisioning_table.scan(Limit=limit)
            items = res.get('Items', [])
            return sorted(items, key=lambda x: x.get('started_at', ''), reverse=True)
        except Exception as e:
            print(f"Error getting provisioning jobs from DynamoDB: {e}")
            return []
