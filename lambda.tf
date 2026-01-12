# lambda handler code zip file
data "archive_file" "lambda_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda.py"
  output_path = "${path.module}/lambda.zip"
}

# define iam lambda role
resource "aws_iam_role" "dkr" {
  name               = format("%s-%s", var.prefix_module, random_string.suffix.result)
  description        = "Allow ECS & Lambda Docker image updates"
  assume_role_policy = data.aws_iam_policy_document.lambda.json
  tags               = var.tags
}
resource "aws_iam_role_policy" "dkr_running" {
  name   = "running"
  role   = aws_iam_role.dkr.id
  policy = data.aws_iam_policy_document.running.json
}
resource "aws_iam_role_policy" "dkr_monitoring" {
  name   = "monitoring"
  role   = aws_iam_role.dkr.id
  policy = data.aws_iam_policy_document.monitoring.json
}

# define lambda function
resource "aws_lambda_function" "dkr" {
  function_name                  = format("%s-%s", var.prefix_module, random_string.suffix.result)
  filename                       = data.archive_file.lambda_handler.output_path
  source_code_hash               = data.archive_file.lambda_handler.output_base64sha256
  role                           = aws_iam_role.dkr.arn
  handler                        = "lambda.handler"
  description                    = "Updates ECS & Lambda Docker images from ECR tags"
  timeout                        = "300"
  memory_size                    = "128"
  runtime                        = var.runtime
  architectures                  = ["arm64"]
  reserved_concurrent_executions = var.concurrents
  tags                           = var.tags
  dead_letter_config {
    target_arn = aws_sqs_queue.dlq.arn
  }
  environment {
    variables = {
      IMAGE_TAG       = var.image_tag
      DISABLE_OLD_ECS = var.disable_old_ecs
      UPDATE_ECS      = var.update_ecs
      UPDATE_LAMBDA   = var.update_lambda
    }
  }
}

# define lambda log group
resource "aws_cloudwatch_log_group" "log" {
  name              = format("/aws/lambda/%s", aws_lambda_function.dkr.function_name)
  tags              = var.tags
  retention_in_days = var.retention
}
