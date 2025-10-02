# Main Lambda function using terraform-aws-modules
module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.0"

  # Basic configuration
  function_name = "${var.app_name}-${var.function_name}"
  description   = var.description
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size

  # Source configuration
  source_path     = "${path.module}/src/python"
  build_in_docker = var.build_in_docker

  # Environment variables
  environment_variables = merge(var.environment_variables, {
    OPENSEARCH_ENDPOINT = var.opensearch_endpoint
    INDEX_NAME          = var.opensearch_index_name
    SEARCH_REGION       = data.aws_region.current.id
    LOG_LEVEL           = var.log_level
    ENVIRONMENT         = var.environment
  })

  # VPC configuration (conditional)
  vpc_subnet_ids         = var.vpc_config != null ? var.vpc_config.subnet_ids : null
  vpc_security_group_ids = var.vpc_config != null ? var.vpc_config.security_group_ids : null

  # IAM policies for OpenSearch and X-Ray
  attach_policy_statements = true
  policy_statements = merge({
    opensearch = {
      effect = "Allow"
      actions = [
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpGet",
        "es:ESHttpHead"
      ]
      resources = [
        "arn:aws:es:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:domain/*"
      ]
    }
    xray = {
      effect = "Allow"
      actions = [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ]
      resources = ["*"]
    }
  }, var.policy_statements)

  # Lambda layers
  layers = var.layers

  # CloudWatch Logs
  cloudwatch_logs_retention_in_days = var.log_retention_days

  # X-Ray tracing
  tracing_mode = var.enable_xray_tracing ? "Active" : "PassThrough"

  # Reserved concurrency
  reserved_concurrent_executions = var.reserved_concurrency

  # Tags
  tags = merge(var.tags, {
    Name      = "${var.app_name}-${var.function_name}"
    Runtime   = var.runtime
    Component = "lambda"
    ManagedBy = "terraform"
  })
}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_monitoring ? 1 : 0

  alarm_name          = "${var.app_name}-${var.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function error rate is too high"

  dimensions = {
    FunctionName = module.lambda.lambda_function_name
  }

  alarm_actions = var.alarm_actions
  ok_actions    = var.alarm_actions

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.enable_monitoring ? 1 : 0

  alarm_name          = "${var.app_name}-${var.function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Average"
  threshold           = var.timeout * 1000 * 0.8 # 80% of timeout in milliseconds

  dimensions = {
    FunctionName = module.lambda.lambda_function_name
  }

  alarm_actions = var.alarm_actions
  tags          = var.tags
}
