# Environment configuration
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-northeast-3"
}

variable "profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "welfan-lg-mfa"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "fuzzy-sku-poc"
}

# OpenSearch configuration
variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
  # Update this with your actual OpenSearch endpoint
  default = "https://search-fuzzy-sku-ppba34qtds6ocweyl62wmgv5we.aos.ap-northeast-3.on.aws"
}

variable "opensearch_index_name" {
  description = "OpenSearch index name"
  type        = string
  default     = "tm-juchum" # Updated to match actual index
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
  default     = ["http://localhost:5173"]
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
  default     = 256
}

variable "lambda_reserved_concurrency" {
  description = "Lambda reserved concurrency"
  type        = number
  default     = 20
}

# Cognito configuration
variable "cognito_mfa_configuration" {
  description = "MFA configuration for Cognito"
  type        = string
  default     = "OFF" # Changed to OFF until MFA methods are properly configured
}

variable "cognito_password_minimum_length" {
  description = "Minimum password length for Cognito"
  type        = number
  default     = 12 # Stronger for production
}

# Monitoring and logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30 # Longer retention for production
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = false
}

# Networking (if needed for Lambda VPC)
variable "vpc_id" {
  description = "VPC ID for Lambda function (recommended for production)"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for Lambda VPC configuration"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for Lambda"
  type        = list(string)
  default     = []
}

# Performance and scaling
variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 2000
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default = {
    CriticalityLevel = "high"
    BackupRequired   = "yes"
    MonitoringLevel  = "enhanced"
  }
}
