# Lambda AI Reranker Module Variables

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "fuzzy-sku-ai-reranker"
}

variable "runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.12"
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "bedrock_region" {
  description = "AWS region for Bedrock client (supports cross-region inference)"
  type        = string
  default     = "ap-northeast-3"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for Claude"
  type        = string
  default     = "anthropic.claude-sonnet-4-5-v1:0"
}

variable "confidence_threshold" {
  description = "Minimum top score for high confidence (topScore > threshold)"
  type        = number
  default     = 25.0
}

variable "score_gap_ratio" {
  description = "Minimum ratio between 1st and 2nd scores (ratio > gap_ratio)"
  type        = number
  default     = 2.0
}

variable "log_level" {
  description = "Lambda logging level (DEBUG, INFO, WARNING, ERROR)"
  type        = string
  default     = "INFO"
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "enable_api_gateway_trigger" {
  description = "Enable API Gateway trigger for Lambda"
  type        = bool
  default     = false
}

variable "api_gateway_source_arn" {
  description = "ARN of API Gateway to allow invocation (required if enable_api_gateway_trigger is true)"
  type        = string
  default     = ""
}

variable "enable_lambda_invoke" {
  description = "Enable Lambda-to-Lambda invocation"
  type        = bool
  default     = true
}

variable "invoking_lambda_arn" {
  description = "ARN of Lambda function that can invoke this reranker (required if enable_lambda_invoke is true)"
  type        = string
  default     = ""
}
