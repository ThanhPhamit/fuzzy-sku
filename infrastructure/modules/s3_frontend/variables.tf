variable "app_name" {}
variable "acm_certificate_arn" {}
variable "route_53_zone_id" {}
variable "domain" {}
variable "create_cloudfront_function" {
  description = "Whether to create the CloudFront function for basic auth"
  type        = bool
  default     = true
}

variable "basic_auth_password" {
  description = "Custom password for basic auth. If not provided, a random password will be generated."
  type        = string
  default     = ""
  sensitive   = true
}

variable "price_class" {
  description = "Price class for CloudFront distribution"
  type        = string
  default     = "PriceClass_All"
}


variable "tags" {
  type        = map(string)
  description = "Tags to apply to resources"
  default     = {}
}
