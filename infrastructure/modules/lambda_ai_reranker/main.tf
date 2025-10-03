# Lambda AI Reranker Module
# Deploys Lambda function with Bedrock Claude Sonnet 4.5 for Japanese SKU search re-ranking

resource "aws_lambda_function" "ai_reranker" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = {
      AWS_REGION           = var.bedrock_region
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      CONFIDENCE_THRESHOLD = var.confidence_threshold
      SCORE_GAP_RATIO      = var.score_gap_ratio
      LOG_LEVEL            = var.log_level
    }
  }

  tags = merge(
    var.tags,
    {
      Name      = var.function_name
      Module    = "lambda_ai_reranker"
      ManagedBy = "Terraform"
    }
  )
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name               = "${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = merge(
    var.tags,
    {
      Name = "${var.function_name}-role"
    }
  )
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Bedrock access policy
resource "aws_iam_role_policy" "bedrock_access" {
  name   = "${var.function_name}-bedrock-access"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.bedrock_access.json
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name = "${var.function_name}-logs"
    }
  )
}

# Lambda Permission for API Gateway (if enabled)
resource "aws_lambda_permission" "api_gateway" {
  count = var.enable_api_gateway_trigger ? 1 : 0

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_reranker.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = var.api_gateway_source_arn
}

# Lambda Permission for other Lambda functions
resource "aws_lambda_permission" "lambda_invoke" {
  count = var.enable_lambda_invoke ? 1 : 0

  statement_id  = "AllowLambdaInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_reranker.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = var.invoking_lambda_arn
}
