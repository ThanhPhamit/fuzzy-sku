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
    BEDROCK_REGION       = var.bedrock_region
    BEDROCK_MODEL_ID     = var.bedrock_model_id
    CONFIDENCE_THRESHOLD = tostring(var.confidence_threshold)
    SCORE_GAP_RATIO      = tostring(var.score_gap_ratio)
    LOG_LEVEL            = var.log_level
    ENVIRONMENT          = var.environment
  })

  # VPC configuration (conditional)
  vpc_subnet_ids         = var.vpc_config != null ? var.vpc_config.subnet_ids : null
  vpc_security_group_ids = var.vpc_config != null ? var.vpc_config.security_group_ids : null

  # IAM policies for Bedrock and X-Ray
  attach_policy_statements = true
  policy_statements = merge({
    bedrock_models = {
      effect = "Allow"
      actions = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      resources = [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
      ]
    }
    bedrock_inference_profiles = {
      effect = "Allow"
      actions = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      resources = [
        "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*"
      ]
    }
    bedrock_list = {
      effect = "Allow"
      actions = [
        "bedrock:GetFoundationModel",
        "bedrock:ListFoundationModels"
      ]
      resources = ["*"]
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
    Component = "lambda-ai-reranker"
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
