

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_route53_zone" "this" {
  name         = var.app_dns_zone
  private_zone = false
}
