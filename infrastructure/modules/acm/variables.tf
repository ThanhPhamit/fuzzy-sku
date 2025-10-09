variable "domain" {}
variable "app_dns_zone" {}
variable "tags" {
  type        = map(string)
  description = "Tags to apply to resources"
  default     = {}
}