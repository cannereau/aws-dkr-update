# define suffix
resource "random_string" "suffix" {
  length  = 6
  lower   = true
  upper   = false
  numeric = false
  special = false
}

# sqs for dead letter queue
resource "aws_sqs_queue" "dlq" {
  name                      = format("%s-%s", var.prefix, random_string.suffix.result)
  sqs_managed_sse_enabled   = true
  message_retention_seconds = 1209600 # maximum value allowed by SQS
  tags                      = var.tags
}

# sqs policy for dead letter queue
resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq.json
}

# event rule
resource "aws_cloudwatch_event_rule" "dkr" {
  name        = format("%s-%s", var.prefix, random_string.suffix.result)
  description = "Catch ECR image update"
  state       = var.event_state
  tags        = var.tags
  event_pattern = jsonencode({
    source      = ["aws.ecr"]
    detail-type = ["ECR Image Action"]
    detail = {
      image-tag   = [var.image_tag]
      action-type = ["PUSH"]
      result      = ["SUCCESS"]
    }
  })
}

# event target
resource "aws_cloudwatch_event_target" "dkr" {
  target_id = format("%s-tgt-%s", var.prefix, random_string.suffix.result)
  rule      = aws_cloudwatch_event_rule.dkr.name
  arn       = aws_lambda_function.dkr.arn
  dead_letter_config {
    arn = aws_sqs_queue.dlq.arn
  }
}

# lambda permission
resource "aws_lambda_permission" "dkr" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dkr.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.dkr.arn
}
