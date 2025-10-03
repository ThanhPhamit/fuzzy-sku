# Get current AWS region
data "aws_region" "current" {}

# Get current AWS account
data "aws_caller_identity" "current" {}

# IAM policy document for CloudWatch Logs
data "aws_iam_policy_document" "api_gateway_logs" {
  count = var.enable_logging ? 1 : 0

  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
      "logs:GetLogEvents",
      "logs:FilterLogEvents"
    ]

    resources = [
      "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/apigateway/${var.app_name}:*"
    ]
  }
}
