# Required variables: app_name, tags
variable "app_name" {
  description = "Application name for resource naming"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Cognito integration
variable "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool for authorization"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  type        = string
}

# API Gateway routes configuration
variable "api_routes" {
  description = <<-EOT
    List of API routes to create. Each route defines a path and integration with Lambda.
    Example:
    [
      {
        path_parts         = ["search", "sku"]  # Creates /search/sku
        http_method        = "GET"
        lambda_function_arn  = "arn:aws:lambda:..."
        lambda_function_name = "search-function"
        authorization      = "COGNITO_USER_POOLS"  # or "NONE"
        request_parameters = {
          "method.request.querystring.q" = true
        }
        request_validator  = "query"  # "query", "body", "both", or "none"
      }
    ]
  EOT
  type = list(object({
    path_parts           = list(string)
    http_method          = string
    lambda_function_arn  = string
    lambda_function_name = string
    authorization        = optional(string, "COGNITO_USER_POOLS")
    request_parameters   = optional(map(bool), {})
    request_validator    = optional(string, "none")
  }))

  validation {
    condition = alltrue([
      for route in var.api_routes :
      contains(["GET", "POST", "PUT", "DELETE", "PATCH"], route.http_method)
    ])
    error_message = "http_method must be one of: GET, POST, PUT, DELETE, PATCH."
  }

  validation {
    condition = alltrue([
      for route in var.api_routes :
      contains(["COGNITO_USER_POOLS", "NONE"], route.authorization)
    ])
    error_message = "authorization must be either COGNITO_USER_POOLS or NONE."
  }

  validation {
    condition = alltrue([
      for route in var.api_routes :
      contains(["query", "body", "both", "none"], route.request_validator)
    ])
    error_message = "request_validator must be one of: query, body, both, none."
  }
}

# API Gateway configuration
variable "api_description" {
  description = "Description for the API Gateway"
  type        = string
  default     = "API Gateway for Lambda functions"
}

variable "stage_name" {
  description = "Stage name for API Gateway deployment"
  type        = string
  default     = "v1"
}

variable "enable_cors" {
  description = "Enable CORS for the API"
  type        = bool
  default     = true
}

variable "cors_allowed_origins" {
  description = "Allowed origins for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allowed_headers" {
  description = "Allowed headers for CORS"
  type        = string
  default     = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
}

variable "throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
  validation {
    condition     = var.throttle_burst_limit >= 0 && var.throttle_burst_limit <= 10000
    error_message = "Throttle burst limit must be between 0 and 10000."
  }
}

variable "throttle_rate_limit" {
  description = "API Gateway throttle rate limit (requests per second)"
  type        = number
  default     = 2000
  validation {
    condition     = var.throttle_rate_limit >= 0 && var.throttle_rate_limit <= 10000
    error_message = "Throttle rate limit must be between 0 and 10000."
  }
}

variable "enable_logging" {
  description = "Enable API Gateway access logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention value."
  }
}

variable "enable_api_key" {
  description = "Enable API key requirement for endpoints"
  type        = bool
  default     = false
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing for API Gateway"
  type        = bool
  default     = false
}
