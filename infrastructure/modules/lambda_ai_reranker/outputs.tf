# Outputs for Lambda AI Reranker Module

output "lambda_function_arn" {
  description = "ARN of the AI reranker Lambda function"
  value       = aws_lambda_function.ai_reranker.arn
}

output "lambda_function_name" {
  description = "Name of the AI reranker Lambda function"
  value       = aws_lambda_function.ai_reranker.function_name
}

output "lambda_function_invoke_arn" {
  description = "Invoke ARN of the AI reranker Lambda function (for API Gateway)"
  value       = aws_lambda_function.ai_reranker.invoke_arn
}

output "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Name of the IAM role for Lambda"
  value       = aws_iam_role.lambda_role.name
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_logs.arn
}

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
