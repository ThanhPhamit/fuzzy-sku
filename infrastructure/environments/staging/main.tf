# Local values for resource naming and tagging
locals {
  name_prefix = "${var.app_name}-${var.environment}"

  # Common tags for all resources
  common_tags = merge({
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "terraform"
    Region      = var.aws_region
  }, var.additional_tags)
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Cognito Authentication Module
module "cognito_auth" {
  source = "../../modules/cognito_auth"

  app_name = local.name_prefix
  tags     = local.common_tags

  # Cognito-specific configuration
  mfa_configuration = var.cognito_mfa_configuration

  password_policy = {
    minimum_length                   = var.cognito_password_minimum_length
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  # OAuth configuration for staging
  callback_urls = [
    "https://localhost:3000/callback",
    "https://staging.your-domain.com/callback"
  ]

  logout_urls = [
    "https://localhost:3000/logout",
    "https://staging.your-domain.com/logout"
  ]

  enable_email_verification = true
}

# Lambda Search Function Module
module "lambda_search" {
  source = "../../modules/lambda_search"

  app_name      = local.name_prefix
  function_name = "search-function"
  description   = "Japanese SKU fuzzy search function - staging"
  tags          = local.common_tags

  # OpenSearch configuration
  opensearch_endpoint   = var.opensearch_endpoint
  opensearch_index_name = var.opensearch_index_name

  # Lambda configuration
  runtime     = "python3.11"
  handler     = "lambda_function.lambda_handler"
  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size
  log_level   = "INFO"
  environment = var.environment

  # Monitoring and logging
  log_retention_days  = var.log_retention_days
  enable_xray_tracing = var.enable_xray_tracing
  enable_monitoring   = true

  # VPC configuration (if needed)
  vpc_config = var.vpc_id != null ? {
    subnet_ids         = var.subnet_ids
    security_group_ids = [] # Add security group IDs if using VPC
  } : null

  # Environment variables for staging
  environment_variables = {
    ENVIRONMENT = var.environment
    DEBUG_MODE  = "true"
  }

  # Build configuration
  build_in_docker = true

  # Reserved concurrency
  reserved_concurrency = var.lambda_reserved_concurrency
}

# API Gateway Module
module "api_gateway" {
  source = "../../modules/api_gateway"

  app_name = local.name_prefix
  tags     = local.common_tags

  # Lambda integration
  lambda_function_arn  = module.lambda_search.lambda_function_arn
  lambda_function_name = module.lambda_search.lambda_function_name

  # Cognito integration
  cognito_user_pool_arn = module.cognito_auth.user_pool_arn
  cognito_user_pool_id  = module.cognito_auth.user_pool_id

  # API Gateway configuration
  stage_name           = var.api_stage_name
  enable_cors          = var.enable_cors
  cors_allowed_origins = var.cors_allowed_origins
  throttle_burst_limit = 1000 # Lower for staging
  throttle_rate_limit  = 500  # Lower for staging
  enable_logging       = true

  api_description = "Japanese SKU Fuzzy Search API - Staging Environment"
}
