import boto3
import json
from datetime import datetime, timedelta
import random
import os

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# Sample log messages
log_messages = {
    'INFO': [
        'Application started successfully',
        'User login successful',
        'Cache refreshed',
        'Data synchronization completed',
        'API request received',
        'Configuration loaded',
        'Background job completed',
        'Health check passed'
    ],
    'WARNING': [
        'High memory usage detected',
        'Slow query execution',
        'Cache miss rate increasing',
        'Large payload size warning',
        'Rate limit approaching',
        'Disk space low',
        'Connection pool nearly full'
    ],
    'ERROR': [
        'Database connection failed',
        'API request timeout',
        'File not found',
        'Resource not found',
        'Data validation error',
        'Network unreachable',
        'Invalid user input',
        'Authentication failed'
    ],
    'CRITICAL': [
        'Emergency shutdown initiated',
        'System crash imminent',
        'Data corruption detected',
        'Security breach attempt',
        'Memory exhaustion',
        'Database deadlock',
        'Service unavailable'
    ]
}

def generate_log_entry(index):
    """Generate a single log entry"""
    # Weighted random selection for log levels
    weights = [0.5, 0.25, 0.15, 0.1]  # INFO, WARNING, ERROR, CRITICAL
    levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level = random.choices(levels, weights=weights)[0]
    
    # Generate timestamp (last 24 hours)
    timestamp = datetime.now() - timedelta(
        hours=random.randint(0, 24),
        minutes=random.randint(0, 60),
        seconds=random.randint(0, 60)
    )
    
    # Select random message for the level
    message = random.choice(log_messages[level])
    
    return {
        'log_id': f"log_{timestamp.timestamp()}_{index}",
        'timestamp': timestamp.isoformat(),
        'level': level,
        'message': message,
        'severity': level,
        'source': random.choice(['application', 'system', 'auth', 'api'])
    }

def populate_logs(count=200):
    """Populate DynamoDB with sample logs"""
    table = dynamodb.Table('CloudLogs')
    
    print(f"Populating CloudLogs with {count} entries...")
    
    for i in range(count):
        log = generate_log_entry(i)
        
        table.put_item(Item={
            'log_id': log['log_id'],
            'timestamp': log['timestamp'],
            'level': log['level'],
            'message': log['message'],
            'severity': log['severity'],
            'source': log['source']
        })
        
        if (i + 1) % 50 == 0:
            print(f"  Added {i + 1}/{count} logs")
    
    print(f"✓ Added {count} logs to CloudLogs")

def populate_alerts(count=10):
    """Populate DynamoDB with sample alerts"""
    table = dynamodb.Table('CloudAlerts')
    
    print(f"Populating CloudAlerts with {count} entries...")
    
    for i in range(count):
        timestamp = datetime.now() - timedelta(
            hours=random.randint(0, 12),
            minutes=random.randint(0, 60)
        )
        
        level = random.choice(['CRITICAL', 'ERROR'])
        message = random.choice(log_messages[level])
        
        table.put_item(Item={
            'alert_id': f"alert_{timestamp.timestamp()}_{i}",
            'timestamp': timestamp.isoformat(),
            'level': level,
            'message': message,
            'source': 'log_analysis'
        })
    
    print(f"✓ Added {count} alerts to CloudAlerts")

def populate_stats():
    """Populate DynamoDB with statistics"""
    table = dynamodb.Table('CloudStats')
    
    print("Populating CloudStats...")
    
    stats = {
        'stat_id': 'latest',
        'total_logs': 200,
        'total_errors': 30,
        'total_warnings': 50,
        'critical_count': 20,
        'most_frequent_errors': [
            {'message': 'Database connection failed', 'count': 8},
            {'message': 'API request timeout', 'count': 5},
            {'message': 'Network unreachable', 'count': 4},
            {'message': 'Resource not found', 'count': 3},
            {'message': 'Authentication failed', 'count': 2}
        ],
        'error_trends': [25, 28, 30, 27, 30],
        'updated_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=stats)
    print("✓ Added statistics to CloudStats")

if __name__ == '__main__':
    print("=" * 50)
    print("Populating DynamoDB with sample data")
    print("=" * 50)
    
    try:
        populate_logs(200)
        populate_alerts(10)
        populate_stats()
        
        print("\n" + "=" * 50)
        print("DynamoDB population complete!")
        print("=" * 50)
        print("\nYou can now view the data in the dashboard.")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure AWS credentials are configured correctly.")
