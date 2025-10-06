# Lambda AI Reranker Module Variables

# Required variables: app_name, tags
variable "app_name" {
  description = "Application name for Lambda naming"
  type        = string
}

variable "function_name" {
  description = "Lambda function name (will be prefixed with app_name)"
  type        = string
  default     = "ai-reranker"
}

variable "tags" {
  description = "Tags to apply to Lambda resources"
  type        = map(string)
  default     = {}
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
  validation {
    condition = contains([
      "python3.9", "python3.10", "python3.11", "python3.12"
    ], var.runtime)
    error_message = "Runtime must be a supported Python Lambda runtime."
  }
}

variable "handler" {
  description = "Lambda function handler"
  type        = string
  default     = "lambda_function.lambda_handler"
}

variable "timeout" {
  description = "Lambda function timeout in seconds (1-900)"
  type        = number
  default     = 30
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "memory_size" {
  description = "Lambda function memory size in MB (128-10240)"
  type        = number
  default     = 512
  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 and 10240 MB."
  }
}

variable "reserved_concurrency" {
  description = "Reserved concurrency for Lambda function"
  type        = number
  default     = -1
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
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing for Lambda function"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}

variable "description" {
  description = "Description for the Lambda function"
  type        = string
  default     = "AI reranker for Japanese SKU search using Bedrock Claude"
}

# VPC configuration (optional)
variable "vpc_config" {
  description = "VPC configuration for Lambda"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "policy_statements" {
  description = "Additional IAM policy statements for Lambda"
  type        = any
  default     = {}
}

variable "layers" {
  description = "List of Lambda layer ARNs"
  type        = list(string)
  default     = []
}

variable "build_in_docker" {
  description = "Build Lambda package in Docker for consistency"
  type        = bool
  default     = true
}

variable "environment_variables" {
  description = "Additional environment variables for Lambda function"
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}
