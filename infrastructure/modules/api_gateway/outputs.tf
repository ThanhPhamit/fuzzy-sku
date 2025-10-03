# ============================================================================
# API GATEWAY OUTPUTS
# ============================================================================
output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.this.id
}

output "api_gateway_arn" {
  description = "ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.this.arn
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.this.execution_arn
}

output "api_gateway_root_resource_id" {
  description = "Root resource ID of the API Gateway"
  value       = aws_api_gateway_rest_api.this.root_resource_id
}

output "api_gateway_url" {
  description = "Base URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.this.id}.execute-api.${data.aws_region.current.region}.amazonaws.com/${var.stage_name}"
}

output "api_gateway_stage_name" {
  description = "Stage name of the API Gateway"
  value       = aws_api_gateway_stage.this.stage_name
}

output "api_gateway_stage_arn" {
  description = "ARN of the API Gateway stage"
  value       = aws_api_gateway_stage.this.arn
}

# ============================================================================
# ROUTE OUTPUTS
# ============================================================================
output "api_endpoints" {
  description = "Map of route paths to their full URLs"
  value = {
    for idx, route in var.api_routes :
    "${route.http_method} /${join("/", route.path_parts)}" => "https://${aws_api_gateway_rest_api.this.id}.execute-api.${data.aws_region.current.region}.amazonaws.com/${var.stage_name}/${join("/", route.path_parts)}"
  }
}

output "resource_ids" {
  description = "Map of resource paths to their IDs"
  value       = local.resource_ids
}

output "method_ids" {
  description = "Map of route indices to method IDs"
  value = {
    for idx, method in aws_api_gateway_method.routes :
    idx => method.id
  }
}

# ============================================================================
# AUTHORIZATION OUTPUTS
# ============================================================================
output "cognito_authorizer_id" {
  description = "ID of the Cognito authorizer"
  value       = aws_api_gateway_authorizer.cognito.id
}

output "cognito_authorizer_arn" {
  description = "ARN of the Cognito authorizer"
  value       = aws_api_gateway_authorizer.cognito.arn
}

# ============================================================================
# API KEY OUTPUTS
# ============================================================================
output "api_key_id" {
  description = "ID of the API key (if enabled)"
  value       = var.enable_api_key ? aws_api_gateway_api_key.this[0].id : null
}

output "api_key_value" {
  description = "Value of the API key (if enabled)"
  value       = var.enable_api_key ? aws_api_gateway_api_key.this[0].value : null
  sensitive   = true
}

output "usage_plan_id" {
  description = "ID of the usage plan (if API key is enabled)"
  value       = var.enable_api_key ? aws_api_gateway_usage_plan.this[0].id : null
}

# ============================================================================
# LOGGING OUTPUTS
# ============================================================================
output "log_group_name" {
  description = "Name of the CloudWatch log group for API Gateway"
  value       = var.enable_logging ? aws_cloudwatch_log_group.api_gateway[0].name : null
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group for API Gateway"
  value       = var.enable_logging ? aws_cloudwatch_log_group.api_gateway[0].arn : null
}

# ============================================================================
# DEPLOYMENT OUTPUTS
# ============================================================================
output "deployment_id" {
  description = "ID of the current deployment"
  value       = aws_api_gateway_deployment.this.id
}

output "deployment_execution_arn" {
  description = "Execution ARN for the deployment"
  value       = aws_api_gateway_rest_api.this.execution_arn
}

# ============================================================================
# REQUEST VALIDATOR OUTPUTS
# ============================================================================
output "request_validator_ids" {
  description = "Map of validator types to their IDs"
  value = {
    query = aws_api_gateway_request_validator.query.id
    body  = aws_api_gateway_request_validator.body.id
    both  = aws_api_gateway_request_validator.both.id
  }
}
