# policy for lambda role identity
data "aws_iam_policy_document" "lambda" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# policy for lambda running privileges
data "aws_iam_policy_document" "running" {
  statement {
    sid    = "LambdaOperations"
    effect = "Allow"
    actions = [
      "lambda:ListFunctions",
      "lambda:GetFunction",
      "lambda:UpdateFunctionCode",
    ]
    resources = ["arn:aws:lambda:*:*:function:*"]
  }
}

# policy for lambda monitoring privileges
data "aws_iam_policy_document" "monitoring" {
  statement {
    sid       = "DLQ"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]
  }
  statement {
    sid    = "Logging"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      format(
        "arn:aws:logs:*:*:log-group:/aws/lambda/%s:log-stream:*",
        aws_lambda_function.dkr.function_name
      )
    ]
  }
}

# policy for dlq
data "aws_iam_policy_document" "dlq" {
  statement {
    sid       = "DLQ"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.dlq.arn]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values = [
        aws_cloudwatch_event_rule.dkr.arn,
        aws_lambda_function.dkr.arn
      ]
    }
  }
}
