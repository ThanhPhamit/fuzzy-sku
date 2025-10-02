# Local values for resource naming and tagging
locals {
  name_prefix = "${var.app_name}-${var.environment}"

  # Common tags for all resources
  common_tags = merge({
    Environment = var.environment
    Project     = var.app_name
    ManagedBy   = "terraform"
    Region      = var.aws_region
  }, var.additional_tags)
}
