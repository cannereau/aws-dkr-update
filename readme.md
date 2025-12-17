# AWS ECR Docker Images automatic updates


This is a Terraform module to build an AWS EventBridge rule
which traps ECR image pushed with **specific tag** and
trigger updates to Lambda functions and ECS tasks  
A common AWS SQS dead letter queue collect
unprocessed *Event* and *Lambda* invocations

> *Warning: don't forget to set up ECR repository policies to allow AWS ECS & Lambda services to pull images*

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0.0 |
| <a name="requirement_archive"></a> [archive](#requirement\_archive) | >= 2.6.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.21.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | >= 3.6.2 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.7.1 |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.26.0 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.7.2 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.dkr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.dkr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_log_group.log](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_iam_role.dkr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.dkr_monitoring](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.dkr_running](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_lambda_function.dkr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_permission.dkr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_sqs_queue.dlq](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue) | resource |
| [aws_sqs_queue_policy.dlq](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue_policy) | resource |
| [random_string.suffix](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/string) | resource |
| [archive_file.lambda_handler](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [aws_iam_policy_document.dlq](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.monitoring](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.running](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_concurrents"></a> [concurrents](#input\_concurrents) | Reserved concurrent Lambda executions | `number` | `4` | no |
| <a name="input_event_state"></a> [event\_state](#input\_event\_state) | EventBridge rule's state. Valid values are ('ENABLED', 'DISABLED') | `string` | `"ENABLED"` | no |
| <a name="input_image_tag"></a> [image\_tag](#input\_image\_tag) | Docker image's tag (e.g. latest, dev, qa, prd, ...) | `string` | `"latest"` | no |
| <a name="input_prefix"></a> [prefix](#input\_prefix) | Prefix for AWS resources | `string` | `"dkr-update"` | no |
| <a name="input_retention"></a> [retention](#input\_retention) | Lambda logs retention in days | `number` | `30` | no |
| <a name="input_runtime"></a> [runtime](#input\_runtime) | Lambda runtime version | `string` | `"python3.14"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags that will be applied to the module's resources | `map(string)` | n/a | yes |
| <a name="input_update_lambda"></a> [update\_lambda](#input\_update\_lambda) | Updates Lambda's image automatically. Valid values are ('on', 'off') | `string` | `"off"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_event_rule"></a> [event\_rule](#output\_event\_rule) | EventBridge rule's ARN |
| <a name="output_lambda_function"></a> [lambda\_function](#output\_lambda\_function) | Lambda function's ARN |
<!-- END_TF_DOCS -->
