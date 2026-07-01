"""
AWS Resources Setup Script
Creates DynamoDB tables and SNS topic
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
sns = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def create_dynamodb_table(table_name, key_name, gsi_name=None, gsi_key=None):
    """Create DynamoDB table with optional GSI"""
    try:
        existing_tables = [table.table_name for table in dynamodb.tables.all()]
        
        if table_name in existing_tables:
            print(f"Table {table_name} already exists")
            return dynamodb.Table(table_name)
        
        table_args = {
            'TableName': table_name,
            'KeySchema': [{'AttributeName': key_name, 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': key_name, 'AttributeType': 'S'}],
            'BillingMode': 'PAY_PER_REQUEST'
        }
        
        # Add GSI if specified
        if gsi_name and gsi_key:
            table_args['AttributeDefinitions'].append({'AttributeName': gsi_key, 'AttributeType': 'S'})
            table_args['GlobalSecondaryIndexes'] = [{
                'IndexName': gsi_name,
                'KeySchema': [{'AttributeName': gsi_key, 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }]
        
        table = dynamodb.create_table(**table_args)
        table.wait_until_exists()
        print(f"Created table: {table_name}")
        return table
        
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return None

def create_sns_topic(topic_name):
    """Create SNS topic for alerts"""
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        print(f"Created SNS topic: {topic_name}")
        print(f"Topic ARN: {topic_arn}")
        return topic_arn
    except sns.exceptions.TopicExistsException:
        print(f"SNS topic {topic_name} already exists")
        response = sns.list_topics()
        for topic in response['Topics']:
            if topic_name in topic['TopicArn']:
                return topic['TopicArn']
    except Exception as e:
        print(f"Error creating SNS topic: {e}")
        return None

def subscribe_email_to_topic(topic_arn, email):
    """Subscribe email to SNS topic"""
    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"Subscribed {email} to topic. Check email for confirmation.")
        return response['SubscriptionArn']
    except Exception as e:
        print(f"Error subscribing email: {e}")
        return None

def main():
    print("Setting up AWS resources for Cloud Log Analyzer...")
    print("-" * 50)
    
    # Create DynamoDB tables
    print("\nCreating DynamoDB tables...")
    logs_table = create_dynamodb_table(
        'CloudLogs', 
        'log_id',
        'SeverityIndex',
        'severity'
    )
    
    alerts_table = create_dynamodb_table(
        'CloudAlerts',
        'alert_id'
    )
    
    stats_table = create_dynamodb_table(
        'CloudStats',
        'stat_id'
    )
    
    # Initialize stats table
    if stats_table:
        stats_table.put_item(Item={
            'stat_id': 'latest',
            'total_logs': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'critical_count': 0,
            'most_frequent_errors': [],
            'error_trends': [],
            'updated_at': 'None'
        })
        print("Initialized stats table")
    
    # Create SNS topic
    print("\nCreating SNS topic...")
    topic_arn = create_sns_topic('log-alerts')
    
    # Subscribe email if provided
    alert_email = os.getenv('ALERT_EMAIL')
    if alert_email and topic_arn:
        print(f"\nSubscribing {alert_email} to alerts...")
        subscribe_email_to_topic(topic_arn, alert_email)
    
    print("\n" + "-" * 50)
    print("AWS resources setup complete!")
    print("\nNext steps:")
    print("1. Update your .env file with the SNS Topic ARN")
    print("2. Deploy the Lambda function")
    print("3. Configure CloudWatch subscription filter")

if __name__ == '__main__':
    main()
