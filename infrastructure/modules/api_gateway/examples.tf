# ============================================================================
# EXAMPLE 1: Simple Search API (Current use case)
# ============================================================================
# This example shows how to use the API Gateway module for the SKU search endpoint
# Usage in environment/main.tf:

/*
module "search_api_gateway" {
  source = "../../modules/api_gateway"

  app_name              = "${var.environment}-${var.app_name}"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  # Single route for SKU search
  api_routes = [
    {
      path_parts           = ["search", "sku"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_search.lambda_function_arn
      lambda_function_name = module.lambda_search.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.querystring.q" = true
      }
      request_validator = "query"
    }
  ]

  # Configuration
  api_description      = "Japanese SKU Fuzzy Search API"
  stage_name           = "v1"
  enable_cors          = true
  cors_allowed_origins = var.cors_allowed_origins
  throttle_burst_limit = var.throttle_burst_limit
  throttle_rate_limit  = var.throttle_rate_limit
  enable_logging       = true
  log_retention_days   = 14

  tags = local.tags
}

# Output the search endpoint URL
output "search_endpoint_url" {
  description = "Full URL for the search endpoint"
  value       = module.search_api_gateway.api_endpoints["GET /search/sku"]
}
*/

# ============================================================================
# EXAMPLE 2: Multiple Routes for RESTful API
# ============================================================================
# This example shows how to create a full CRUD API with multiple Lambda functions

/*
module "api_gateway" {
  source = "../../modules/api_gateway"

  app_name              = "${var.environment}-${var.app_name}"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  api_routes = [
    # Search endpoint
    {
      path_parts           = ["search", "sku"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_search.lambda_function_arn
      lambda_function_name = module.lambda_search.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.querystring.q" = true
      }
      request_validator = "query"
    },
    # Create SKU
    {
      path_parts           = ["sku"]
      http_method          = "POST"
      lambda_function_arn  = module.lambda_create_sku.lambda_function_arn
      lambda_function_name = module.lambda_create_sku.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_validator    = "body"
    },
    # Get SKU by ID
    {
      path_parts           = ["sku", "{id}"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_get_sku.lambda_function_arn
      lambda_function_name = module.lambda_get_sku.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.id" = true
      }
      request_validator = "query"
    },
    # Update SKU
    {
      path_parts           = ["sku", "{id}"]
      http_method          = "PUT"
      lambda_function_arn  = module.lambda_update_sku.lambda_function_arn
      lambda_function_name = module.lambda_update_sku.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.id" = true
      }
      request_validator = "both"
    },
    # Delete SKU
    {
      path_parts           = ["sku", "{id}"]
      http_method          = "DELETE"
      lambda_function_arn  = module.lambda_delete_sku.lambda_function_arn
      lambda_function_name = module.lambda_delete_sku.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.id" = true
      }
      request_validator = "query"
    },
    # Health check (no auth required)
    {
      path_parts           = ["health"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_health.lambda_function_arn
      lambda_function_name = module.lambda_health.lambda_function_name
      authorization        = "NONE"
      request_validator    = "none"
    }
  ]

  stage_name            = "v1"
  enable_cors           = true
  cors_allowed_origins  = ["https://yourdomain.com", "http://localhost:3000"]
  throttle_burst_limit  = 10000
  throttle_rate_limit   = 5000
  enable_logging        = true
  enable_xray_tracing   = true

  tags = local.tags
}

# Output all endpoint URLs
output "api_endpoints" {
  description = "All API endpoint URLs"
  value       = module.api_gateway.api_endpoints
}
*/

# ============================================================================
# EXAMPLE 3: Staging vs Production Configuration
# ============================================================================

## Staging Environment
/*
module "api_gateway_staging" {
  source = "../../modules/api_gateway"

  app_name              = "staging-wms"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  api_routes = [
    {
      path_parts           = ["search", "sku"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_search.lambda_function_arn
      lambda_function_name = module.lambda_search.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters   = { "method.request.querystring.q" = true }
      request_validator    = "query"
    }
  ]

  stage_name           = "staging"
  enable_cors          = true
  cors_allowed_origins = ["*"]  # Allow all origins in staging for testing
  throttle_burst_limit = 5000
  throttle_rate_limit  = 2000
  enable_logging       = true
  log_retention_days   = 7
  enable_xray_tracing  = false
  enable_api_key       = false

  tags = {
    Environment = "staging"
    Project     = "wms"
    ManagedBy   = "terraform"
  }
}
*/

## Production Environment
/*
module "api_gateway_production" {
  source = "../../modules/api_gateway"

  app_name              = "production-wms"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  api_routes = [
    {
      path_parts           = ["search", "sku"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_search.lambda_function_arn
      lambda_function_name = module.lambda_search.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters   = { "method.request.querystring.q" = true }
      request_validator    = "query"
    }
  ]

  stage_name           = "v1"
  enable_cors          = true
  cors_allowed_origins = ["https://wms.production.example.com"]  # Restrict to production domain
  throttle_burst_limit = 20000  # Higher limits for production
  throttle_rate_limit  = 10000
  enable_logging       = true
  log_retention_days   = 30  # Longer retention for compliance
  enable_xray_tracing  = true  # Enable tracing for production
  enable_api_key       = true  # Additional security layer

  tags = {
    Environment = "production"
    Project     = "wms"
    ManagedBy   = "terraform"
    CostCenter  = "engineering"
    Backup      = "daily"
  }
}

# Store API key in Systems Manager Parameter Store
resource "aws_ssm_parameter" "api_key" {
  name        = "/wms/production/api-key"
  description = "Production API Gateway key"
  type        = "SecureString"
  value       = module.api_gateway_production.api_key_value

  tags = {
    Environment = "production"
    Project     = "wms"
  }
}
*/

# ============================================================================
# EXAMPLE 4: Advanced Configuration with Path Parameters
# ============================================================================

/*
module "advanced_api_gateway" {
  source = "../../modules/api_gateway"

  app_name              = "${var.environment}-wms"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  api_routes = [
    # Product catalog search
    {
      path_parts           = ["catalog", "search"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_catalog_search.lambda_function_arn
      lambda_function_name = module.lambda_catalog_search.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.querystring.q"        = true
        "method.request.querystring.category" = false
        "method.request.querystring.limit"    = false
      }
      request_validator = "query"
    },
    # Category list
    {
      path_parts           = ["catalog", "categories"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_categories.lambda_function_arn
      lambda_function_name = module.lambda_categories.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_validator    = "none"
    },
    # Product details by category and SKU
    {
      path_parts           = ["catalog", "{category}", "{sku}"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_product_detail.lambda_function_arn
      lambda_function_name = module.lambda_product_detail.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.category" = true
        "method.request.path.sku"      = true
      }
      request_validator = "query"
    },
    # Bulk update
    {
      path_parts           = ["catalog", "bulk"]
      http_method          = "POST"
      lambda_function_arn  = module.lambda_bulk_update.lambda_function_arn
      lambda_function_name = module.lambda_bulk_update.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_validator    = "body"
    }
  ]

  api_description       = "Advanced Product Catalog API"
  stage_name            = "v1"
  enable_cors           = true
  cors_allowed_origins  = var.cors_origins
  cors_allowed_headers  = "Content-Type,Authorization,X-Api-Key,X-Request-ID"
  throttle_burst_limit  = 15000
  throttle_rate_limit   = 7500
  enable_logging        = true
  log_retention_days    = 30
  enable_xray_tracing   = true
  enable_api_key        = var.environment == "production" ? true : false

  tags = merge(local.common_tags, {
    API = "catalog"
  })
}

# Export endpoints for frontend configuration
output "catalog_api_config" {
  value = {
    base_url    = module.advanced_api_gateway.api_gateway_url
    endpoints   = module.advanced_api_gateway.api_endpoints
    api_key_id  = module.advanced_api_gateway.api_key_id
    authorizer  = module.advanced_api_gateway.cognito_authorizer_id
  }
  sensitive = true
}
*/

# ============================================================================
# EXAMPLE 5: Using Different Validators
# ============================================================================

/*
module "api_gateway_with_validators" {
  source = "../../modules/api_gateway"

  app_name              = "${var.environment}-wms"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  api_routes = [
    # Query validator - for GET requests with query parameters
    {
      path_parts           = ["search"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_search.lambda_function_arn
      lambda_function_name = module.lambda_search.lambda_function_name
      request_parameters   = { "method.request.querystring.q" = true }
      request_validator    = "query"  # Validates query parameters only
    },
    # Body validator - for POST/PUT requests with JSON body
    {
      path_parts           = ["products"]
      http_method          = "POST"
      lambda_function_arn  = module.lambda_create.lambda_function_arn
      lambda_function_name = module.lambda_create.lambda_function_name
      request_validator    = "body"  # Validates request body only
    },
    # Both validator - for PUT requests with path params and body
    {
      path_parts           = ["products", "{id}"]
      http_method          = "PUT"
      lambda_function_arn  = module.lambda_update.lambda_function_arn
      lambda_function_name = module.lambda_update.lambda_function_name
      request_parameters   = { "method.request.path.id" = true }
      request_validator    = "both"  # Validates both query/path params and body
    },
    # None validator - for simple endpoints without validation
    {
      path_parts           = ["health"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_health.lambda_function_arn
      lambda_function_name = module.lambda_health.lambda_function_name
      authorization        = "NONE"
      request_validator    = "none"  # No validation
    }
  ]

  stage_name = "v1"
  tags       = local.tags
}
*/
