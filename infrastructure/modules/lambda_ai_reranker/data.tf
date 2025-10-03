# Data sources for Lambda AI Reranker Module

# Package Lambda function code
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/src/python"
  output_path = "${path.module}/builds/${var.function_name}.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache", "tests"]
}

# IAM assume role policy for Lambda
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# IAM policy for Bedrock access
data "aws_iam_policy_document" "bedrock_access" {
  statement {
    effect = "Allow"

    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]

    resources = [
      "arn:aws:bedrock:*::foundation-model/${var.bedrock_model_id}",
      "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "bedrock:GetFoundationModel",
      "bedrock:ListFoundationModels"
    ]

    resources = ["*"]
  }
}

# Get current AWS region
data "aws_region" "current" {}

# Get current AWS account ID
data "aws_caller_identity" "current" {}
