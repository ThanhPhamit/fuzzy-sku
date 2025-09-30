# Environment configuration
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-northeast-3"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "fuzzy-sku"
}

# OpenSearch configuration
variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
  # Update this with your actual OpenSearch endpoint
  default = "https://search-fuzzy-sku-staging.ap-northeast-3.es.amazonaws.com"
}

variable "opensearch_index_name" {
  description = "OpenSearch index name"
  type        = string
  default     = "japanese_sku_index"
}

# API Gateway configuration
variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "v1"
}

variable "enable_cors" {
  description = "Enable CORS for API Gateway"
  type        = bool
  default     = true
}

variable "cors_allowed_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"] # Restrict this in production
}

# Lambda configuration
variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_reserved_concurrency" {
  description = "Lambda reserved concurrency"
  type        = number
  default     = 5
}

# Cognito configuration
variable "cognito_mfa_configuration" {
  description = "MFA configuration for Cognito"
  type        = string
  default     = "OPTIONAL"
}

variable "cognito_password_minimum_length" {
  description = "Minimum password length for Cognito"
  type        = number
  default     = 8
}

# Monitoring and logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

# Networking (if needed for Lambda VPC)
variable "vpc_id" {
  description = "VPC ID for Lambda function (optional)"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for Lambda VPC configuration"
  type        = list(string)
  default     = []
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
