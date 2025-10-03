# API Gateway Module for Lambda Functions

## 📋 Overview

This is a **reusable, flexible API Gateway module** designed to work with multiple Lambda functions. It supports dynamic route configuration, Cognito authentication, CORS, request validation, throttling, and comprehensive logging.

## ✨ Features

- ✅ **Dynamic Route Configuration**: Define multiple routes with different paths, methods, and Lambda integrations
- ✅ **Cognito Authentication**: Built-in support for Cognito User Pool authorization
- ✅ **CORS Support**: Automatic OPTIONS method creation for all routes
- ✅ **Request Validation**: Query parameters, body, or both validation
- ✅ **Throttling**: Configurable rate and burst limits
- ✅ **Logging**: CloudWatch Logs integration with structured access logs
- ✅ **X-Ray Tracing**: Optional distributed tracing support
- ✅ **API Key Support**: Optional API key authentication
- ✅ **Multiple Lambda Functions**: Support different Lambda functions for different routes

## 🏗️ Module Structure

```
modules/api_gateway/
├── main.tf           # Main resources with dynamic route creation
├── variables.tf      # Input variable declarations
├── outputs.tf        # Output value exports
├── data.tf           # Data sources
├── versions.tf       # Provider version constraints
└── README.md         # This file
```

## 📝 Usage Examples

### Example 1: Simple Search API (GET /search/sku)

```hcl
module "search_api_gateway" {
  source = "../modules/api_gateway"

  app_name              = "${var.environment}-${var.app_name}"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  # Define a single route for SKU search
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

  # API Gateway settings
  stage_name            = "v1"
  enable_cors           = true
  cors_allowed_origins  = ["https://yourdomain.com", "http://localhost:3000"]
  throttle_burst_limit  = 5000
  throttle_rate_limit   = 2000

  tags = local.tags
}
```

### Example 2: Multiple Routes with Different Lambda Functions

```hcl
module "api_gateway" {
  source = "../modules/api_gateway"

  app_name              = "${var.environment}-${var.app_name}"
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id

  # Define multiple routes
  api_routes = [
    # GET /search/sku - Search endpoint
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
    # POST /products - Create product
    {
      path_parts           = ["products"]
      http_method          = "POST"
      lambda_function_arn  = module.lambda_create_product.lambda_function_arn
      lambda_function_name = module.lambda_create_product.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_validator    = "body"
    },
    # GET /products/{id} - Get product by ID
    {
      path_parts           = ["products", "{id}"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_get_product.lambda_function_arn
      lambda_function_name = module.lambda_get_product.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.id" = true
      }
      request_validator = "query"
    },
    # PUT /products/{id} - Update product
    {
      path_parts           = ["products", "{id}"]
      http_method          = "PUT"
      lambda_function_arn  = module.lambda_update_product.lambda_function_arn
      lambda_function_name = module.lambda_update_product.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.id" = true
      }
      request_validator = "both"
    },
    # DELETE /products/{id} - Delete product
    {
      path_parts           = ["products", "{id}"]
      http_method          = "DELETE"
      lambda_function_arn  = module.lambda_delete_product.lambda_function_arn
      lambda_function_name = module.lambda_delete_product.lambda_function_name
      authorization        = "COGNITO_USER_POOLS"
      request_parameters = {
        "method.request.path.id" = true
      }
      request_validator = "query"
    },
    # GET /health - Health check (no auth)
    {
      path_parts           = ["health"]
      http_method          = "GET"
      lambda_function_arn  = module.lambda_health.lambda_function_arn
      lambda_function_name = module.lambda_health.lambda_function_name
      authorization        = "NONE"
      request_validator    = "none"
    }
  ]

  # API Gateway settings
  stage_name            = "v1"
  enable_cors           = true
  cors_allowed_origins  = ["https://yourdomain.com"]
  throttle_burst_limit  = 10000
  throttle_rate_limit   = 5000
  enable_logging        = true
  enable_xray_tracing   = true

  tags = local.tags
}
```

### Example 3: Production Configuration with Enhanced Security

```hcl
module "api_gateway" {
  source = "../modules/api_gateway"

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
      request_parameters = {
        "method.request.querystring.q" = true
      }
      request_validator = "query"
    }
  ]

  # API Gateway configuration
  api_description = "Production API Gateway for WMS"
  stage_name      = "v1"

  # CORS - Restricted origins for production
  enable_cors          = true
  cors_allowed_origins = ["https://wms.production.example.com"]
  cors_allowed_headers = "Content-Type,Authorization,X-Api-Key"

  # Throttling - Higher limits for production
  throttle_burst_limit = 20000
  throttle_rate_limit  = 10000

  # Logging and monitoring
  enable_logging      = true
  log_retention_days  = 30
  enable_xray_tracing = true

  # API Key - Additional security layer
  enable_api_key = true

  tags = {
    Environment = "production"
    Project     = "wms"
    ManagedBy   = "terraform"
    CostCenter  = "engineering"
    Backup      = "daily"
  }
}
```

## 📋 Variables

### Required Variables

| Variable                | Type         | Description                                    |
| ----------------------- | ------------ | ---------------------------------------------- |
| `app_name`              | string       | Application name for resource naming           |
| `cognito_user_pool_arn` | string       | ARN of the Cognito User Pool for authorization |
| `cognito_user_pool_id`  | string       | ID of the Cognito User Pool                    |
| `api_routes`            | list(object) | List of API routes to create (see below)       |

### api_routes Object Structure

Each route in `api_routes` has the following structure:

```hcl
{
  path_parts           = ["segment1", "segment2"]  # Path segments, e.g., ["search", "sku"] = /search/sku
  http_method          = "GET"                      # HTTP method: GET, POST, PUT, DELETE, PATCH
  lambda_function_arn  = "arn:aws:lambda:..."      # Lambda function ARN
  lambda_function_name = "function-name"            # Lambda function name
  authorization        = "COGNITO_USER_POOLS"       # Optional: Authorization type (default: "COGNITO_USER_POOLS")
  request_parameters   = {                          # Optional: Request parameters
    "method.request.querystring.q" = true
  }
  request_validator    = "query"                    # Optional: "query", "body", "both", "none" (default: "none")
}
```

### Optional Variables

| Variable               | Type         | Default                                                                  | Description                                          |
| ---------------------- | ------------ | ------------------------------------------------------------------------ | ---------------------------------------------------- |
| `tags`                 | map(string)  | `{}`                                                                     | Tags to apply to all resources                       |
| `api_description`      | string       | `"API Gateway for Lambda functions"`                                     | Description for the API Gateway                      |
| `stage_name`           | string       | `"v1"`                                                                   | Stage name for API Gateway deployment                |
| `enable_cors`          | bool         | `true`                                                                   | Enable CORS for the API                              |
| `cors_allowed_origins` | list(string) | `["*"]`                                                                  | Allowed origins for CORS                             |
| `cors_allowed_headers` | string       | `"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"` | Allowed headers for CORS                             |
| `throttle_burst_limit` | number       | `5000`                                                                   | API Gateway throttle burst limit (0-10000)           |
| `throttle_rate_limit`  | number       | `2000`                                                                   | API Gateway throttle rate limit per second (0-10000) |
| `enable_logging`       | bool         | `true`                                                                   | Enable API Gateway access logging                    |
| `log_retention_days`   | number       | `14`                                                                     | CloudWatch log retention in days                     |
| `enable_api_key`       | bool         | `false`                                                                  | Enable API key requirement for endpoints             |
| `enable_xray_tracing`  | bool         | `false`                                                                  | Enable X-Ray tracing for API Gateway                 |

## 📤 Outputs

### API Gateway Information

| Output                      | Description                      |
| --------------------------- | -------------------------------- |
| `api_gateway_id`            | ID of the API Gateway            |
| `api_gateway_arn`           | ARN of the API Gateway           |
| `api_gateway_execution_arn` | Execution ARN of the API Gateway |
| `api_gateway_url`           | Base URL of the API Gateway      |
| `api_gateway_stage_name`    | Stage name of the API Gateway    |

### Route Information

| Output          | Description                           |
| --------------- | ------------------------------------- |
| `api_endpoints` | Map of route paths to their full URLs |
| `resource_ids`  | Map of resource paths to their IDs    |
| `method_ids`    | Map of route indices to method IDs    |

### Authorization

| Output                  | Description                  |
| ----------------------- | ---------------------------- |
| `cognito_authorizer_id` | ID of the Cognito authorizer |

### API Key (if enabled)

| Output          | Description                      |
| --------------- | -------------------------------- |
| `api_key_id`    | ID of the API key                |
| `api_key_value` | Value of the API key (sensitive) |
| `usage_plan_id` | ID of the usage plan             |

### Logging

| Output           | Description                      |
| ---------------- | -------------------------------- |
| `log_group_name` | Name of the CloudWatch log group |
| `log_group_arn`  | ARN of the CloudWatch log group  |

## 🔍 How to Use Outputs

```hcl
# Get the search endpoint URL
output "search_endpoint" {
  value = module.api_gateway.api_endpoints["GET /search/sku"]
}

# Get all API endpoints
output "all_endpoints" {
  value = module.api_gateway.api_endpoints
}

# Get API base URL for frontend configuration
output "api_base_url" {
  value = module.api_gateway.api_gateway_url
}

# Get API key for client applications (if enabled)
output "api_key" {
  value     = module.api_gateway.api_key_value
  sensitive = true
}
```

## 🎯 How It Works

### 1. **Dynamic Resource Creation**

The module uses `for_each` to dynamically create API Gateway resources based on the `api_routes` variable:

- Automatically creates resource hierarchies (e.g., `/search` → `/search/sku`)
- Deduplicates shared path segments
- Creates proper parent-child relationships

### 2. **Request Validation**

Three types of validators are created:

- `query`: Validates query parameters only
- `body`: Validates request body only
- `both`: Validates both query parameters and body

### 3. **CORS Support**

When `enable_cors = true`:

- Automatically creates OPTIONS methods for all routes
- Configures proper CORS headers
- Supports custom allowed origins and headers

### 4. **Lambda Integration**

- Uses AWS_PROXY integration for seamless Lambda integration
- Automatically grants API Gateway permission to invoke Lambda functions
- Supports different Lambda functions for different routes

## 🔒 Security Best Practices

### 1. **Cognito Authorization**

```hcl
authorization = "COGNITO_USER_POOLS"  # Require authentication
```

### 2. **Restricted CORS Origins**

```hcl
cors_allowed_origins = ["https://yourdomain.com"]  # Don't use "*" in production
```

### 3. **Request Validation**

```hcl
request_validator = "both"  # Validate all inputs
```

### 4. **API Key Protection**

```hcl
enable_api_key = true  # Additional security layer
```

### 5. **Rate Limiting**

```hcl
throttle_burst_limit = 5000
throttle_rate_limit  = 2000
```

## 📊 Monitoring and Logging

### CloudWatch Logs

When `enable_logging = true`, the module creates:

- CloudWatch Log Group
- Structured access logs with request details
- IAM policy for API Gateway to write logs

### X-Ray Tracing

When `enable_xray_tracing = true`:

- End-to-end request tracing
- Performance analysis
- Bottleneck identification

### CloudWatch Metrics

Automatically enabled for all routes:

- Invocation count
- Error rate
- Latency
- Integration latency

## 🔄 Update Strategy

To add a new route:

1. Add the route to `api_routes`:

```hcl
api_routes = [
  # Existing routes...
  {
    path_parts           = ["new", "endpoint"]
    http_method          = "POST"
    lambda_function_arn  = module.new_lambda.lambda_function_arn
    lambda_function_name = module.new_lambda.lambda_function_name
  }
]
```

2. Run `terraform plan` to review changes
3. Run `terraform apply` to deploy

The module will automatically:

- Create new resources
- Update the deployment
- Maintain existing routes

## 📝 Notes

- **Path Parameters**: Use `{parameter}` syntax for path parameters (e.g., `["products", "{id}"]`)
- **Shared Paths**: Multiple routes can share path segments (e.g., `/products` for GET and POST)
- **Deployment Triggers**: Changes to routes automatically trigger redeployment
- **Lambda Permissions**: Module automatically creates necessary Lambda permissions

## 🐛 Troubleshooting

### Issue: Routes not accessible

**Solution**: Check if Lambda permissions are correctly set. The module should automatically create them.

### Issue: CORS errors

**Solution**: Verify `cors_allowed_origins` includes your frontend domain and protocol (http/https).

### Issue: 403 Forbidden

**Solution**: Ensure Cognito user pool is correctly configured and tokens are valid.

### Issue: 429 Too Many Requests

**Solution**: Increase `throttle_burst_limit` and `throttle_rate_limit` values.

## 📚 Additional Resources

- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Lambda Proxy Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)

---

**Module Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintained By**: Lion Garden Inc.
