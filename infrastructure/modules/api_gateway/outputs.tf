# Export all important information that other modules need
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

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.this.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.stage_name}"
}

output "api_gateway_stage_name" {
  description = "Stage name of the API Gateway"
  value       = aws_api_gateway_stage.this.stage_name
}

output "search_endpoint_url" {
  description = "Full URL for the search endpoint"
  value       = "https://${aws_api_gateway_rest_api.this.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.stage_name}/search/sku"
}

output "authorizer_id" {
  description = "ID of the Cognito authorizer"
  value       = aws_api_gateway_authorizer.cognito.id
}

output "log_group_name" {
  description = "Name of the CloudWatch log group for API Gateway"
  value       = var.enable_logging ? aws_cloudwatch_log_group.api_gateway[0].name : null
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group for API Gateway"
  value       = var.enable_logging ? aws_cloudwatch_log_group.api_gateway[0].arn : null
}
