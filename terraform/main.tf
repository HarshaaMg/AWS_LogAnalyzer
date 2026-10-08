terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# DynamoDB Tables
resource "aws_dynamodb_table" "cloud_logs" {
  name           = "CloudLogs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "log_id"

  attribute {
    name = "log_id"
    type = "S"
  }

  attribute {
    name = "severity"
    type = "S"
  }

  global_secondary_index {
    name               = "SeverityIndex"
    hash_key           = "severity"
    projection_type    = "ALL"
  }

  tags = {
    Name        = "CloudLogs"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "cloud_alerts" {
  name           = "CloudAlerts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "alert_id"

  attribute {
    name = "alert_id"
    type = "S"
  }

  tags = {
    Name        = "CloudAlerts"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "cloud_stats" {
  name           = "CloudStats"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "stat_id"

  attribute {
    name = "stat_id"
    type = "S"
  }

  tags = {
    Name        = "CloudStats"
    Environment = var.environment
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "log_alerts" {
  name = "log-alerts"

  tags = {
    Name        = "LogAlerts"
    Environment = var.environment
  }
}

# SNS Subscription for Email
resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.log_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "application_logs" {
  name              = "/aws/cloud-log-analyzer/application"
  retention_in_days = 7

  tags = {
    Name        = "ApplicationLogs"
    Environment = var.environment
  }
}

# Lambda Function
resource "aws_lambda_function" "log_processor" {
  filename         = "../lambda/log_processor.zip"
  function_name    = "log-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "log_processor.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.log_alerts.arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = {
    Name        = "LogProcessor"
    Environment = var.environment
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/log-processor"
  retention_in_days = 7
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "lambda-log-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "LambdaLogProcessorRole"
    Environment = var.environment
  }
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_dynamodb_sns" {
  name = "lambda-dynamodb-sns-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.cloud_logs.arn,
          aws_dynamodb_table.cloud_alerts.arn,
          aws_dynamodb_table.cloud_stats.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.log_alerts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Logs Subscription Filter
resource "aws_cloudwatch_log_subscription_filter" "lambda_subscription" {
  name            = "lambda-subscription-filter"
  log_group_name  = aws_cloudwatch_log_group.application_logs.name
  filter_pattern  = ""
  destination_arn = aws_lambda_function.log_processor.arn

  depends_on = [
    aws_lambda_permission.allow_cloudwatch
  ]
}

# Permission for CloudWatch to invoke Lambda
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_processor.function_name
  principal     = "logs.amazonaws.com"
  source_arn    = aws_cloudwatch_log_group.application_logs.arn
}

# API Gateway
resource "aws_apigatewayv2_api" "log_analyzer_api" {
  name          = "cloud-log-analyzer-api"
  protocol_type = "HTTP"

  tags = {
    Name        = "CloudLogAnalyzerAPI"
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.log_analyzer_api.id
  name        = "prod"
  auto_deploy = true
}

# ==============================================================================
# Linux Observability & Auto-Scaling Tables
# ==============================================================================
resource "aws_dynamodb_table" "cloud_hosts" {
  name         = "CloudHosts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "host_id"

  attribute {
    name = "host_id"
    type = "S"
  }

  tags = {
    Name        = "CloudHosts"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "cloud_metrics" {
  name         = "CloudResourceMetrics"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "host_id"
  range_key    = "timestamp"

  attribute {
    name = "host_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name        = "CloudResourceMetrics"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "cloud_scaling_events" {
  name         = "CloudScalingEvents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "event_id"
  range_key    = "timestamp"

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name        = "CloudScalingEvents"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "cloud_incidents" {
  name         = "CloudIncidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"
  range_key    = "start_time"

  attribute {
    name = "incident_id"
    type = "S"
  }

  attribute {
    name = "start_time"
    type = "S"
  }

  tags = {
    Name        = "CloudIncidents"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "cloud_provisioning" {
  name         = "CloudProvisioning"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "provisioning_id"
  range_key    = "started_at"

  attribute {
    name = "provisioning_id"
    type = "S"
  }

  attribute {
    name = "started_at"
    type = "S"
  }

  tags = {
    Name        = "CloudProvisioning"
    Environment = var.environment
  }
}

# Security Group for Auto-Scaled Linux VMs
resource "aws_security_group" "linux_vm_sg" {
  name        = "linux-observability-vm-sg"
  description = "Security group for auto-scaled Linux VMs"

  ingress {
    description = "Node Exporter metrics"
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "LinuxObservabilityVM"
    Environment = var.environment
  }
}

# IAM Role & Instance Profile for EC2 Linux Instances
resource "aws_iam_role" "ec2_worker_role" {
  name = "ec2-linux-observability-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_worker_profile" {
  name = "LogAnalyzerInstanceProfile"
  role = aws_iam_role.ec2_worker_role.name
}
