# ============================================================================
# LOCALS - Process routes and build resource hierarchy
# ============================================================================
locals {
  # Create flat list of all path parts with their full paths and depth
  all_path_parts = flatten([
    for route_idx, route in var.api_routes : [
      for part_idx, part in route.path_parts : {
        route_index = route_idx
        part_index  = part_idx
        depth       = part_idx
        part        = part
        full_path   = join("/", slice(route.path_parts, 0, part_idx + 1))
        parent_path = part_idx == 0 ? "" : join("/", slice(route.path_parts, 0, part_idx))
      }
    ]
  ])

  # Flatten all unique paths
  unique_paths = distinct([for item in local.all_path_parts : item.full_path])

  # Create map of path -> resource details for easy lookup (deduplicated)
  path_resources_map = {
    for path in local.unique_paths :
    path => {
      for item in local.all_path_parts :
      item.full_path => {
        part        = item.part
        parent_path = item.parent_path
        depth       = item.depth
      } if item.full_path == path
    }
  }

  path_resources_unique = {
    for path, details_map in local.path_resources_map :
    path => values(details_map)[0]
  }

  # Group paths by depth level
  paths_level_0 = [for path, details in local.path_resources_unique : path if details.depth == 0]
  paths_level_1 = [for path, details in local.path_resources_unique : path if details.depth == 1]
  paths_level_2 = [for path, details in local.path_resources_unique : path if details.depth == 2]
  paths_level_3 = [for path, details in local.path_resources_unique : path if details.depth == 3]
  paths_level_4 = [for path, details in local.path_resources_unique : path if details.depth == 4]

  # Collect all HTTP methods that need CORS
  cors_methods = var.enable_cors ? distinct(flatten([
    for route in var.api_routes : [route.http_method, "OPTIONS"]
  ])) : []
}

# ============================================================================
# API GATEWAY REST API
# ============================================================================
resource "aws_api_gateway_rest_api" "this" {
  name        = "${var.app_name}-api"
  description = var.api_description

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(var.tags, {
    Name      = "${var.app_name}-api-gateway"
    Component = "api"
  })
}

# ============================================================================
# COGNITO AUTHORIZER
# ============================================================================
resource "aws_api_gateway_authorizer" "cognito" {
  name          = "${var.app_name}-cognito-authorizer"
  rest_api_id   = aws_api_gateway_rest_api.this.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [var.cognito_user_pool_arn]
}

# ============================================================================
# API GATEWAY RESOURCES - Create resources level by level to avoid cycles
# ============================================================================

# Level 0: Direct children of root (e.g., /search, /products)
resource "aws_api_gateway_resource" "level_0" {
  for_each = toset(local.paths_level_0)

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = local.path_resources_unique[each.key].part
}

# Level 1: Children of level 0 (e.g., /search/sku, /products/list)
resource "aws_api_gateway_resource" "level_1" {
  for_each = toset(local.paths_level_1)

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.level_0[local.path_resources_unique[each.key].parent_path].id
  path_part   = local.path_resources_unique[each.key].part
}

# Level 2: Children of level 1 (e.g., /search/sku/advanced)
resource "aws_api_gateway_resource" "level_2" {
  for_each = toset(local.paths_level_2)

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.level_1[local.path_resources_unique[each.key].parent_path].id
  path_part   = local.path_resources_unique[each.key].part
}

# Level 3: Children of level 2 (e.g., /api/v1/search/sku)
resource "aws_api_gateway_resource" "level_3" {
  for_each = toset(local.paths_level_3)

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.level_2[local.path_resources_unique[each.key].parent_path].id
  path_part   = local.path_resources_unique[each.key].part
}

# Level 4: Children of level 3 (for very deep paths)
resource "aws_api_gateway_resource" "level_4" {
  for_each = toset(local.paths_level_4)

  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_resource.level_3[local.path_resources_unique[each.key].parent_path].id
  path_part   = local.path_resources_unique[each.key].part
}

# Helper local to get resource ID by path
locals {
  resource_ids = merge(
    { for k, v in aws_api_gateway_resource.level_0 : k => v.id },
    { for k, v in aws_api_gateway_resource.level_1 : k => v.id },
    { for k, v in aws_api_gateway_resource.level_2 : k => v.id },
    { for k, v in aws_api_gateway_resource.level_3 : k => v.id },
    { for k, v in aws_api_gateway_resource.level_4 : k => v.id }
  )
}

# ============================================================================
# REQUEST VALIDATORS
# ============================================================================
resource "aws_api_gateway_request_validator" "query" {
  name                        = "${var.app_name}-query-validator"
  rest_api_id                 = aws_api_gateway_rest_api.this.id
  validate_request_body       = false
  validate_request_parameters = true
}

resource "aws_api_gateway_request_validator" "body" {
  name                        = "${var.app_name}-body-validator"
  rest_api_id                 = aws_api_gateway_rest_api.this.id
  validate_request_body       = true
  validate_request_parameters = false
}

resource "aws_api_gateway_request_validator" "both" {
  name                        = "${var.app_name}-both-validator"
  rest_api_id                 = aws_api_gateway_rest_api.this.id
  validate_request_body       = true
  validate_request_parameters = true
}

# ============================================================================
# API METHODS - Dynamic creation for each route
# ============================================================================
resource "aws_api_gateway_method" "routes" {
  for_each = { for idx, route in var.api_routes : idx => route }

  rest_api_id      = aws_api_gateway_rest_api.this.id
  resource_id      = local.resource_ids[join("/", each.value.path_parts)]
  http_method      = each.value.http_method
  authorization    = each.value.authorization
  authorizer_id    = each.value.authorization == "COGNITO_USER_POOLS" ? aws_api_gateway_authorizer.cognito.id : null
  api_key_required = var.enable_api_key

  request_parameters = each.value.request_parameters

  request_validator_id = (
    each.value.request_validator == "query" ? aws_api_gateway_request_validator.query.id :
    each.value.request_validator == "body" ? aws_api_gateway_request_validator.body.id :
    each.value.request_validator == "both" ? aws_api_gateway_request_validator.both.id :
    null
  )
}

# ============================================================================
# LAMBDA INTEGRATIONS - Connect methods to Lambda functions
# ============================================================================
resource "aws_api_gateway_integration" "routes" {
  for_each = { for idx, route in var.api_routes : idx => route }

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = local.resource_ids[join("/", each.value.path_parts)]
  http_method = aws_api_gateway_method.routes[each.key].http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.id}:lambda:path/2015-03-31/functions/${each.value.lambda_function_arn}/invocations"
}

# ============================================================================
# LAMBDA PERMISSIONS - Allow API Gateway to invoke Lambda functions
# ============================================================================
resource "aws_lambda_permission" "api_gateway" {
  for_each = { for idx, route in var.api_routes : idx => route }

  statement_id  = "AllowExecutionFromAPIGateway-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.this.execution_arn}/*/${each.value.http_method}/${join("/", each.value.path_parts)}"
}

# ============================================================================
# CORS SUPPORT - OPTIONS methods for CORS preflight
# ============================================================================
resource "aws_api_gateway_method" "options" {
  for_each = var.enable_cors ? toset(local.unique_paths) : toset([])

  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = local.resource_ids[each.key]
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  for_each = var.enable_cors ? toset(local.unique_paths) : toset([])

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = local.resource_ids[each.key]
  http_method = aws_api_gateway_method.options[each.key].http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({ statusCode = 200 })
  }
}

resource "aws_api_gateway_method_response" "options" {
  for_each = var.enable_cors ? toset(local.unique_paths) : toset([])

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = local.resource_ids[each.key]
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options" {
  for_each = var.enable_cors ? toset(local.unique_paths) : toset([])

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = local.resource_ids[each.key]
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = aws_api_gateway_method_response.options[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'${var.cors_allowed_headers}'"
    "method.response.header.Access-Control-Allow-Methods" = "'${join(",", local.cors_methods)}'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${join(",", var.cors_allowed_origins)}'"
  }
}

# ============================================================================
# API GATEWAY DEPLOYMENT
# ============================================================================
resource "aws_api_gateway_deployment" "this" {
  depends_on = [
    aws_api_gateway_method.routes,
    aws_api_gateway_integration.routes,
    aws_api_gateway_method.options,
    aws_api_gateway_integration.options,
  ]

  rest_api_id = aws_api_gateway_rest_api.this.id

  triggers = {
    # Redeploy when routes configuration changes
    redeployment = sha1(jsonencode({
      routes     = var.api_routes
      cors       = var.enable_cors
      origins    = var.cors_allowed_origins
      api_key    = var.enable_api_key
      updated_at = timestamp()
    }))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# API GATEWAY STAGE
# ============================================================================
resource "aws_api_gateway_stage" "this" {
  deployment_id = aws_api_gateway_deployment.this.id
  rest_api_id   = aws_api_gateway_rest_api.this.id
  stage_name    = var.stage_name

  xray_tracing_enabled = var.enable_xray_tracing

  access_log_settings {
    destination_arn = var.enable_logging ? aws_cloudwatch_log_group.api_gateway[0].arn : null
    format = var.enable_logging ? jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    }) : null
  }

  tags = merge(var.tags, {
    Name      = "${var.app_name}-${var.stage_name}"
    Component = "api-gateway-stage"
  })
}

# ============================================================================
# METHOD SETTINGS - Throttling, Logging, Metrics
# ============================================================================
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  stage_name  = aws_api_gateway_stage.this.stage_name
  method_path = "*/*"

  settings {
    # Throttling
    throttling_burst_limit = var.throttle_burst_limit
    throttling_rate_limit  = var.throttle_rate_limit

    # Logging
    logging_level      = var.enable_logging ? "INFO" : "OFF"
    data_trace_enabled = var.enable_logging

    # Metrics
    metrics_enabled = true

    # Caching (disabled by default, can be enabled per method if needed)
    caching_enabled = false
  }
}

# ============================================================================
# CLOUDWATCH LOGS
# ============================================================================
resource "aws_cloudwatch_log_group" "api_gateway" {
  count             = var.enable_logging ? 1 : 0
  name              = "/aws/apigateway/${var.app_name}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name      = "${var.app_name}-api-logs"
    Component = "api-gateway-logs"
  })
}

# CloudWatch Log Resource Policy for API Gateway
resource "aws_cloudwatch_log_resource_policy" "api_gateway" {
  count           = var.enable_logging ? 1 : 0
  policy_name     = "${var.app_name}-api-gateway-logs"
  policy_document = data.aws_iam_policy_document.api_gateway_logs[0].json
}

# ============================================================================
# API KEY (Optional)
# ============================================================================
resource "aws_api_gateway_api_key" "this" {
  count = var.enable_api_key ? 1 : 0
  name  = "${var.app_name}-api-key"

  tags = merge(var.tags, {
    Name      = "${var.app_name}-api-key"
    Component = "api-gateway-key"
  })
}

resource "aws_api_gateway_usage_plan" "this" {
  count = var.enable_api_key ? 1 : 0
  name  = "${var.app_name}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.this.id
    stage  = aws_api_gateway_stage.this.stage_name
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }

  throttle_settings {
    burst_limit = var.throttle_burst_limit
    rate_limit  = var.throttle_rate_limit
  }

  tags = merge(var.tags, {
    Name      = "${var.app_name}-usage-plan"
    Component = "api-gateway-usage-plan"
  })
}

resource "aws_api_gateway_usage_plan_key" "this" {
  count         = var.enable_api_key ? 1 : 0
  key_id        = aws_api_gateway_api_key.this[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.this[0].id
}
