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
  #checkov:skip=CKV_AWS_356: Ensure no IAM policies documents allow "*" as a statement's resource for restrictable actions
  statement {
    sid    = "LambdaRead"
    effect = "Allow"
    actions = [
      "lambda:ListFunctions"
    ]
    resources = ["*"]
  }
  statement {
    sid    = "LambdaUpdate"
    effect = "Allow"
    actions = [
      "lambda:GetFunction",
      "lambda:UpdateFunctionCode"
    ]
    resources = ["arn:aws:lambda:*:*:function:*"]
  }
  statement {
    sid    = "ECSRead"
    effect = "Allow"
    actions = [
      "ecs:ListClusters",
      "ecs:ListServices",
      "ecs:ListTaskDefinitions",
      "ecs:DescribeTaskDefinition",
      "ecs:DescribeServices"
    ]
    resources = ["*"]
  }
  statement {
    sid    = "ECSUpdate"
    effect = "Allow"
    actions = [
      "ecs:UpdateService"
    ]
    resources = ["arn:aws:ecs:*:*:service/*"]
  }
  statement {
    sid    = "ECSPassRole"
    effect = "Allow"
    actions = [
      "iam:PassRole"
    ]
    resources = [
      format("arn:aws:iam::*:role/%s*", var.prefix_ecs)
    ]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      variable = "iam:AssociatedResourceARN"
      values   = ["arn:aws:ecs:*:*:task-definition/*"]
    }

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
        "arn:aws:logs:*:*:log-group:/aws/lambda/%s-%s:log-stream:*",
        var.prefix_module,
        random_string.suffix.result
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
