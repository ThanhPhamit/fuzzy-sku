# Local values for naming
locals {
  user_pool_name = var.user_pool_name != null ? var.user_pool_name : "${var.app_name}-user-pool"
  client_name    = var.client_name != null ? var.client_name : "${var.app_name}-client"
  domain_name    = var.domain_name != null ? var.domain_name : "${var.app_name}-${random_string.domain_suffix.result}"
}

# Random string for domain name uniqueness
resource "random_string" "domain_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Cognito User Pool
resource "aws_cognito_user_pool" "this" {
  name = local.user_pool_name

  # Allow users to sign in with email address
  username_attributes = var.allow_email_as_username ? ["email"] : null

  # Password policy
  password_policy {
    minimum_length                   = var.password_policy.minimum_length
    require_lowercase                = var.password_policy.require_lowercase
    require_numbers                  = var.password_policy.require_numbers
    require_symbols                  = var.password_policy.require_symbols
    require_uppercase                = var.password_policy.require_uppercase
    temporary_password_validity_days = var.password_policy.temporary_password_validity_days
  }

  # MFA configuration
  mfa_configuration = var.mfa_configuration

  # Account recovery settings
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Admin create user config
  admin_create_user_config {
    allow_admin_create_user_only = false

    invite_message_template {
      email_message = "Your username is {username} and temporary password is {####}. Please sign in and change your password."
      email_subject = "Your temporary password for ${var.app_name}"
      sms_message   = "Your username is {username} and temporary password is {####}"
    }
  }

  # Email configuration
  dynamic "email_configuration" {
    for_each = var.enable_email_verification ? [1] : []
    content {
      email_sending_account = "COGNITO_DEFAULT"
    }
  }

  # Auto verified attributes
  auto_verified_attributes = var.enable_email_verification ? ["email"] : []

  # User attributes - preserving existing schema to prevent modification errors
  # AWS Cognito User Pool schema attributes are immutable after creation
  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "name"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "preferred_username"
    required            = false
    mutable             = true
  }

  # Lifecycle management to ignore schema changes since they are immutable
  lifecycle {
    ignore_changes = [schema]
  }

  # Verification message template
  dynamic "verification_message_template" {
    for_each = var.enable_email_verification ? [1] : []
    content {
      default_email_option = "CONFIRM_WITH_CODE"
      email_message        = var.email_verification_message
      email_subject        = var.email_verification_subject
    }
  }

  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"
  }

  # Deletion protection - configurable for easier testing/development
  deletion_protection = var.deletion_protection

  tags = merge(var.tags, {
    Name      = "${var.app_name}-user-pool"
    Component = "authentication"
  })
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "this" {
  name         = local.client_name
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = var.generate_secret

  # OAuth configuration - conditional based on whether OAuth flows are enabled
  supported_identity_providers = var.supported_identity_providers

  # Only set OAuth configuration if flows are specified and URLs are provided
  callback_urls                        = length(var.allowed_oauth_flows) > 0 && length(var.callback_urls) > 0 ? var.callback_urls : null
  logout_urls                          = length(var.allowed_oauth_flows) > 0 && length(var.logout_urls) > 0 ? var.logout_urls : null
  allowed_oauth_flows                  = length(var.allowed_oauth_flows) > 0 && length(var.callback_urls) > 0 ? var.allowed_oauth_flows : null
  allowed_oauth_scopes                 = length(var.allowed_oauth_flows) > 0 && length(var.callback_urls) > 0 ? var.allowed_oauth_scopes : null
  allowed_oauth_flows_user_pool_client = length(var.allowed_oauth_flows) > 0 && length(var.callback_urls) > 0 ? true : false

  # Token validity
  access_token_validity  = var.token_validity.access_token
  id_token_validity      = var.token_validity.id_token
  refresh_token_validity = var.token_validity.refresh_token

  token_validity_units {
    access_token  = var.token_validity_units.access_token
    id_token      = var.token_validity_units.id_token
    refresh_token = var.token_validity_units.refresh_token
  }

  # Explicit auth flows
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Read and write attributes
  read_attributes = [
    "email",
    "email_verified",
    "name",
    "preferred_username"
  ]

  write_attributes = [
    "email",
    "name",
    "preferred_username"
  ]
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "this" {
  count        = var.enable_user_pool_domain ? 1 : 0
  domain       = local.domain_name
  user_pool_id = aws_cognito_user_pool.this.id
}

# Cognito Identity Pool (for unauthenticated access if needed)
resource "aws_cognito_identity_pool" "this" {
  identity_pool_name               = "${var.app_name}-identity-pool"
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.this.id
    provider_name           = aws_cognito_user_pool.this.endpoint
    server_side_token_check = false
  }

  tags = merge(var.tags, {
    Name      = "${var.app_name}-identity-pool"
    Component = "authentication"
  })
}

# IAM role for authenticated users
resource "aws_iam_role" "authenticated" {
  name = "${var.app_name}-cognito-authenticated-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.this.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name      = "${var.app_name}-cognito-authenticated-role"
    Component = "authentication"
  })
}

# IAM policy for authenticated users
resource "aws_iam_role_policy" "authenticated" {
  name = "${var.app_name}-cognito-authenticated-policy"
  role = aws_iam_role.authenticated.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-sync:*",
          "cognito-identity:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach roles to identity pool
resource "aws_cognito_identity_pool_roles_attachment" "this" {
  identity_pool_id = aws_cognito_identity_pool.this.id

  roles = {
    "authenticated" = aws_iam_role.authenticated.arn
  }

  depends_on = [
    aws_iam_role.authenticated
  ]
}
