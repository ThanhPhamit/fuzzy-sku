# Required variables: app_name, tags
variable "app_name" {
  description = "Application name for Lambda naming"
  type        = string
}

variable "function_name" {
  description = "Lambda function name (will be prefixed with app_name)"
  type        = string
  default     = "search-function"
}

variable "tags" {
  description = "Tags to apply to Lambda resources"
  type        = map(string)
  default     = {}
}

# OpenSearch configuration
variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
}

variable "opensearch_index_name" {
  description = "OpenSearch index name for SKU data"
  type        = string
  default     = "japanese_sku_index"
}

# Lambda configuration
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
  default     = 10
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
  description = "IAM policy statements for Lambda"
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
  description = "Environment variables for Lambda function"
  type        = map(string)
  default     = {}
  sensitive   = true
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
  default     = "Japanese SKU fuzzy search function"
}

variable "log_level" {
  description = "Log level for Lambda function"
  type        = string
  default     = "INFO"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}
