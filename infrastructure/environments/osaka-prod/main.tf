module "acm" {
  source = "../../modules/acm"

  domain       = var.app_cert_dns_domain # cert for zone root domain
  app_dns_zone = var.app_dns_zone

  providers = {
    aws          = aws
    aws.virginia = aws.virginia
  }

  tags = local.common_tags
}


module "s3_frontend" {
  source = "../../modules/s3_frontend"

  app_name                   = local.name_prefix
  acm_certificate_arn        = module.acm.virginia_certificate_arn
  route_53_zone_id           = data.aws_route53_zone.this.id
  domain                     = var.frontend_domain
  create_cloudfront_function = false
  basic_auth_password        = var.basic_auth_password
  price_class                = var.price_class

  tags = local.common_tags

  depends_on = [module.acm]
}

# Cognito Authentication Module
module "cognito_auth" {
  source = "../../modules/cognito_auth"

  app_name = local.name_prefix
  tags     = local.common_tags

  # Enable email-based login
  allow_email_as_username = true

  # Production Cognito configuration
  mfa_configuration = var.cognito_mfa_configuration

  password_policy = {
    minimum_length                   = var.cognito_password_minimum_length
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 3 # Shorter for production
  }

  # For production, override callback URLs when you have actual domain
  # callback_urls = ["https://yourdomain.com/callback"]
  # logout_urls = ["https://yourdomain.com/logout"]

  enable_email_verification = true

  # Public client configuration - no OAuth flows
  generate_secret     = false
  allowed_oauth_flows = []
  callback_urls       = []
  logout_urls         = []

  # Production token validity (shorter for security)
  token_validity = {
    access_token  = 1 # 1 hour
    id_token      = 1 # 1 hour
    refresh_token = 7 # 7 days
  }

  # Deletion protection - set to INACTIVE for easier testing/development
  # For production, consider setting to ACTIVE to prevent accidental deletion
  deletion_protection = "INACTIVE"
}

# Lambda AI Reranker Module
module "lambda_ai_reranker" {
  source = "../../modules/lambda_ai_reranker"

  app_name      = local.name_prefix
  function_name = "ai-reranker"
  description   = "AI reranker for Japanese SKU search using Bedrock Claude - production"
  tags          = local.common_tags

  # Lambda configuration
  runtime     = "python3.12"
  handler     = "lambda_function.lambda_handler"
  timeout     = var.lambda_timeout
  memory_size = 512
  log_level   = "INFO"
  environment = var.environment

  # Bedrock configuration - using global inference profile for Claude Sonnet 4.5
  bedrock_region   = var.aws_region                                     # Use ap-northeast-3 (local region)
  bedrock_model_id = "global.anthropic.claude-sonnet-4-5-20250929-v1:0" # Global inference profile for Claude Sonnet 4.5

  # Confidence thresholds
  confidence_threshold = 25.0
  score_gap_ratio      = 2.0

  # Monitoring and logging
  log_retention_days  = var.log_retention_days
  enable_xray_tracing = var.enable_xray_tracing
  enable_monitoring   = true

  # Build configuration
  build_in_docker = true

  # Reserved concurrency
  reserved_concurrency = -1
}

# Lambda Search Function Module
module "lambda_search" {
  source = "../../modules/lambda_search"

  app_name      = local.name_prefix
  function_name = "search-function"
  description   = "Japanese SKU fuzzy search function - production"
  tags          = local.common_tags

  # OpenSearch configuration
  opensearch_endpoint   = var.opensearch_endpoint
  opensearch_index_name = var.opensearch_index_name

  # Production Lambda configuration
  runtime     = "python3.12"
  handler     = "lambda_function.lambda_handler"
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size
  log_level   = "INFO"
  environment = var.environment

  # Monitoring and logging
  log_retention_days  = var.log_retention_days
  enable_xray_tracing = var.enable_xray_tracing
  enable_monitoring   = true

  # VPC configuration for production security
  vpc_config = var.vpc_id != null ? {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  } : null

  # AI Reranker configuration
  ai_reranker_function_name = module.lambda_ai_reranker.lambda_function_name
  ai_reranker_function_arn  = module.lambda_ai_reranker.lambda_function_arn

  # Production environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
    DEBUG_MODE  = "false"
    CACHE_TTL   = "300" # 5 minutes cache
  }

  # Build configuration
  build_in_docker = true

  # Reserved concurrency
  reserved_concurrency = var.lambda_reserved_concurrency

  # Ensure AI reranker is created first
  depends_on = [module.lambda_ai_reranker]
}

# Additional Lambda permission for search function to invoke reranker
resource "aws_lambda_permission" "search_invoke_reranker" {
  statement_id  = "AllowSearchLambdaInvokeReranker"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_ai_reranker.lambda_function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = module.lambda_search.lambda_function_arn
}

# API Gateway Module - Using new flexible module
module "api_gateway" {
  source = "../../modules/api_gateway"

  app_name = local.name_prefix
  tags     = local.common_tags

  # Cognito integration
  cognito_user_pool_arn = module.cognito_auth.user_pool_arn
  cognito_user_pool_id  = module.cognito_auth.user_pool_id

  # Define API routes - flexible configuration for multiple endpoints
  api_routes = [
    {
      path_parts           = ["search", "sku"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_search.lambda_function_arn
      lambda_function_name = module.lambda_search.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.querystring.q" = true
      }
      request_validator = "query"
    }
  ]

  # Production API Gateway configuration
  api_description      = "Japanese SKU Fuzzy Search API - Production Environment"
  stage_name           = var.api_stage_name
  enable_cors          = var.enable_cors
  cors_allowed_origins = var.cors_allowed_origins
  cors_allowed_headers = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"

  # Throttling configuration
  throttle_burst_limit = var.api_throttle_burst_limit
  throttle_rate_limit  = var.api_throttle_rate_limit

  # Logging and monitoring
  enable_logging      = true
  log_retention_days  = var.log_retention_days
  enable_xray_tracing = var.enable_xray_tracing

  # Security
  enable_api_key = false # Set to true if you want additional API key layer
}

# CloudWatch Dashboard for Production Monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", module.lambda_search.lambda_function_name],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", "${local.name_prefix}-api"],
            [".", "Latency", ".", "."],
            [".", "4XXError", ".", "."],
            [".", "5XXError", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Gateway Metrics"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms for Production Monitoring
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    FunctionName = module.lambda_search.lambda_function_name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${local.name_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors API Gateway 5XX errors"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ApiName = "${local.name_prefix}-api"
  }

  tags = local.common_tags
}
