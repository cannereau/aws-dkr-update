output "event_rule" {
  value       = aws_cloudwatch_event_rule.dkr.arn
  description = "EventBridge rule's ARN"
}

output "lambda_function" {
  value       = aws_lambda_function.dkr.arn
  description = "Lambda function's ARN"
}
