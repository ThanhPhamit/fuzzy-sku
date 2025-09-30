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

# User pool configuration
variable "user_pool_name" {
  description = "Name for the Cognito User Pool"
  type        = string
  default     = null
}

variable "password_policy" {
  description = "Password policy configuration"
  type = object({
    minimum_length                   = number
    require_lowercase                = bool
    require_numbers                  = bool
    require_symbols                  = bool
    require_uppercase                = bool
    temporary_password_validity_days = number
  })
  default = {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }
}

variable "mfa_configuration" {
  description = "MFA configuration (OFF, ON, OPTIONAL)"
  type        = string
  default     = "OPTIONAL"
  validation {
    condition     = contains(["OFF", "ON", "OPTIONAL"], var.mfa_configuration)
    error_message = "MFA configuration must be OFF, ON, or OPTIONAL."
  }
}

variable "enable_email_verification" {
  description = "Enable email verification for user registration"
  type        = bool
  default     = true
}

variable "email_verification_message" {
  description = "Email verification message template"
  type        = string
  default     = "Your verification code is {####}"
}

variable "email_verification_subject" {
  description = "Email verification subject"
  type        = string
  default     = "Your verification code"
}

# User pool client configuration
variable "client_name" {
  description = "Name for the Cognito User Pool Client"
  type        = string
  default     = null
}

variable "generate_secret" {
  description = "Generate a client secret for the user pool client"
  type        = bool
  default     = false
}

variable "supported_identity_providers" {
  description = "List of supported identity providers"
  type        = list(string)
  default     = ["COGNITO"]
}

variable "callback_urls" {
  description = "List of allowed callback URLs"
  type        = list(string)
  default     = ["https://localhost:3000/callback"]
}

variable "logout_urls" {
  description = "List of allowed logout URLs"
  type        = list(string)
  default     = ["https://localhost:3000/logout"]
}

variable "allowed_oauth_flows" {
  description = "List of allowed OAuth flows"
  type        = list(string)
  default     = ["code"]
}

variable "allowed_oauth_scopes" {
  description = "List of allowed OAuth scopes"
  type        = list(string)
  default     = ["email", "openid", "profile"]
}

variable "token_validity_units" {
  description = "Token validity time units"
  type = object({
    access_token  = string
    id_token      = string
    refresh_token = string
  })
  default = {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}

variable "token_validity" {
  description = "Token validity durations"
  type = object({
    access_token  = number
    id_token      = number
    refresh_token = number
  })
  default = {
    access_token  = 1
    id_token      = 1
    refresh_token = 30
  }
}

# Domain configuration
variable "enable_user_pool_domain" {
  description = "Enable Cognito User Pool domain"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the user pool (if not provided, will use app_name)"
  type        = string
  default     = null
}
