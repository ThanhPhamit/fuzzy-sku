output "bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "bucket_regional_domain_name" {
  value = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "bucket_id" {
  value = aws_s3_bucket.frontend.id
}