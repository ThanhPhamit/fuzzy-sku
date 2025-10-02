# Export all important information that other modules need
output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.this.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.this.endpoint
}

output "user_pool_domain" {
  description = "Domain of the Cognito User Pool"
  value       = var.enable_user_pool_domain ? aws_cognito_user_pool_domain.this[0].domain : null
}

output "hosted_ui_url" {
  description = "Hosted UI URL for the user pool"
  value       = var.enable_user_pool_domain ? "https://${aws_cognito_user_pool_domain.this[0].domain}.auth.${data.aws_region.current.id}.amazoncognito.com" : null
}

output "user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.this.id
}

output "user_pool_client_secret" {
  description = "Secret of the Cognito User Pool Client (if generated)"
  value       = var.generate_secret ? aws_cognito_user_pool_client.this.client_secret : null
  sensitive   = true
}

output "identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = aws_cognito_identity_pool.this.id
}

output "authenticated_role_arn" {
  description = "ARN of the IAM role for authenticated users"
  value       = aws_iam_role.authenticated.arn
}

output "login_url" {
  description = "Login URL for the application"
  value       = var.enable_user_pool_domain && length(var.callback_urls) > 0 ? "${aws_cognito_user_pool_domain.this[0].domain}.auth.${data.aws_region.current.id}.amazoncognito.com/login?client_id=${aws_cognito_user_pool_client.this.id}&response_type=code&scope=email+openid+profile&redirect_uri=${var.callback_urls[0]}" : null
}

output "logout_url" {
  description = "Logout URL for the application"
  value       = var.enable_user_pool_domain && length(var.logout_urls) > 0 ? "${aws_cognito_user_pool_domain.this[0].domain}.auth.${data.aws_region.current.id}.amazoncognito.com/logout?client_id=${aws_cognito_user_pool_client.this.id}&logout_uri=${var.logout_urls[0]}" : null
}
