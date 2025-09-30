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
  value       = module.cognito_auth.user_pool_hosted_ui_url
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

# Logging outputs
output "api_gateway_log_group" {
  description = "CloudWatch log group for API Gateway"
  value       = module.api_gateway.log_group_name
}

output "lambda_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = module.lambda_search.log_group_name
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
