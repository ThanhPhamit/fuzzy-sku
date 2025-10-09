output "certificate_id" {
  value = aws_acm_certificate.this.id
}

output "certificate_arn" {
  value = aws_acm_certificate.this.arn
}

output "virginia_certificate_arn" {
  value = aws_acm_certificate.virginia.arn
}
