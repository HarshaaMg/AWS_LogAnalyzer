output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    logs   = aws_dynamodb_table.cloud_logs.name
    alerts = aws_dynamodb_table.cloud_alerts.name
    stats  = aws_dynamodb_table.cloud_stats.name
  }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.log_alerts.arn
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.log_processor.function_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.application_logs.name
}

output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_stage.lambda.invoke_url
}
