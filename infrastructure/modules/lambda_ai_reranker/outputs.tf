# Export all important information that other modules need
output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = module.lambda.lambda_function_arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = module.lambda.lambda_function_name
}

output "lambda_function_invoke_arn" {
  description = "The invoke ARN of the Lambda function"
  value       = module.lambda.lambda_function_invoke_arn
}

output "lambda_function_version" {
  description = "Latest published version of Lambda function"
  value       = module.lambda.lambda_function_version
}

output "lambda_role_arn" {
  description = "The ARN of the IAM role created for the Lambda function"
  value       = module.lambda.lambda_role_arn
}

output "lambda_cloudwatch_log_group_arn" {
  description = "The ARN of the CloudWatch Log Group"
  value       = module.lambda.lambda_cloudwatch_log_group_arn
}

output "lambda_cloudwatch_log_group_name" {
  description = "The name of the CloudWatch Log Group"
  value       = module.lambda.lambda_cloudwatch_log_group_name
}

# Legacy outputs for backwards compatibility
output "lambda_function_qualified_arn" {
  description = "Qualified ARN of the Lambda function"
  value       = module.lambda.lambda_function_qualified_arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = module.lambda.lambda_role_name
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.lambda.lambda_cloudwatch_log_group_name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = module.lambda.lambda_cloudwatch_log_group_arn
}

# AI Reranker specific outputs
output "bedrock_model_id" {
  description = "Bedrock model ID configured for this Lambda"
  value       = var.bedrock_model_id
}

output "bedrock_region" {
  description = "AWS region configured for Bedrock client"
  value       = var.bedrock_region
}

output "confidence_config" {
  description = "Confidence threshold configuration"
  value = {
    threshold = var.confidence_threshold
    gap_ratio = var.score_gap_ratio
  }
}
