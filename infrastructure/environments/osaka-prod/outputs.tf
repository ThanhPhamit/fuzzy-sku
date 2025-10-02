# API Gateway outputs
output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = module.api_gateway.api_gateway_url
}

output "search_endpoint_url" {
  description = "Full URL for the search endpoint"
  value       = module.api_gateway.search_endpoint_url
}

# Cognito outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.cognito_auth.user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = module.cognito_auth.user_pool_client_id
}

output "cognito_hosted_ui_url" {
  description = "Hosted UI URL for user authentication"
  value       = module.cognito_auth.hosted_ui_url
}

output "cognito_login_url" {
  description = "Login URL"
  value       = module.cognito_auth.login_url
}

output "cognito_logout_url" {
  description = "Logout URL"
  value       = module.cognito_auth.logout_url
}

# Lambda outputs
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda_search.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.lambda_search.lambda_function_arn
}

# Monitoring outputs
output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "api_gateway_log_group" {
  description = "CloudWatch log group for API Gateway"
  value       = module.api_gateway.log_group_name
}

output "lambda_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = module.lambda_search.log_group_name
}

# Security outputs
output "cognito_identity_pool_id" {
  description = "Cognito Identity Pool ID"
  value       = module.cognito_auth.identity_pool_id
}

output "authenticated_role_arn" {
  description = "IAM role ARN for authenticated users"
  value       = module.cognito_auth.authenticated_role_arn
}

# Environment information
output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "deployment_timestamp" {
  description = "Deployment timestamp"
  value       = timestamp()
}

# Performance configuration
output "lambda_memory_size" {
  description = "Lambda memory configuration"
  value       = var.lambda_memory_size
}

output "lambda_reserved_concurrency" {
  description = "Lambda reserved concurrency"
  value       = var.lambda_reserved_concurrency
}

output "api_throttle_limits" {
  description = "API Gateway throttle configuration"
  value = {
    burst_limit = var.api_throttle_burst_limit
    rate_limit  = var.api_throttle_rate_limit
  }
}
