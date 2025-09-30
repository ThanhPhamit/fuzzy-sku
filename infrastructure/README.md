# Japanese SKU Fuzzy Search Infrastructure

This directory contains the Terraform infrastructure code for deploying the Japanese SKU fuzzy search system to AWS.

## Architecture Overview

The infrastructure consists of three main components:

### 1. **AWS Cognito Authentication**

- User Pool for authentication and authorization
- User Pool Client for application integration
- Identity Pool for AWS resource access
- MFA support (optional in staging, enforced in production)
- OAuth 2.0 / OIDC integration

### 2. **AWS Lambda Search Function**

- Python 3.11 runtime with OpenSearch integration
- Multi-analyzer Japanese text search capabilities
- VPC configuration support for security
- X-Ray tracing for performance monitoring
- Auto-scaling with reserved concurrency

### 3. **AWS API Gateway**

- REST API with Cognito authorization
- CORS support for web applications
- Throttling and rate limiting
- CloudWatch logging and monitoring
- Regional endpoint for optimal performance

## Directory Structure

```
infrastructure/
├── modules/                    # Reusable Terraform modules
│   ├── api_gateway/           # API Gateway module
│   ├── cognito_auth/          # Cognito authentication module
│   └── lambda_search/         # Lambda search function module
├── environments/              # Environment-specific configurations
│   ├── staging/               # Staging environment
│   └── production/            # Production environment
├── deploy.sh                  # Deployment automation script
└── README.md                  # This file
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **OpenSearch domain** already deployed and accessible
4. **S3 bucket** for Terraform state storage (update backend configuration)
5. **DynamoDB table** for state locking (optional but recommended)

## Configuration

### 1. Update Backend Configuration

Edit the `backend` configuration in `environments/*/providers.tf`:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "fuzzy-sku/{environment}/terraform.tfstate"
  region         = "ap-northeast-3"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

### 2. Update OpenSearch Endpoints

Edit the `opensearch_endpoint` variable in `environments/*/variables.tf`:

```hcl
variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
  default     = "https://search-fuzzy-sku-{env}.ap-northeast-3.es.amazonaws.com"
}
```

### 3. Configure Callback URLs

Update the callback URLs in `environments/*/main.tf` for your actual domain:

```hcl
callback_urls = [
  "https://your-domain.com/callback"
]

logout_urls = [
  "https://your-domain.com/logout"
]
```

## Deployment

### Automated Deployment

Use the provided deployment script:

```bash
# Deploy to staging
./deploy.sh staging

# Deploy to production
./deploy.sh production
```

### Manual Deployment

For manual deployment or troubleshooting:

```bash
# Navigate to environment directory
cd environments/staging  # or production

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply

# View outputs
terraform output
```

## Environment Differences

### Staging Environment

- Lower resource allocations for cost optimization
- Relaxed security settings for development
- MFA optional
- CORS allows all origins (\*)
- Debug mode enabled
- Shorter log retention

### Production Environment

- Higher resource allocations for performance
- Enhanced security settings
- MFA enforced
- CORS restricted to specific domains
- Debug mode disabled
- Longer log retention
- CloudWatch monitoring and alarms
- VPC configuration recommended

## Key Outputs

After deployment, you'll receive these important URLs and identifiers:

- **API Gateway URL**: Base URL for the API
- **Search Endpoint URL**: Direct URL for SKU search
- **Cognito Login URL**: User authentication URL
- **Cognito User Pool ID**: For client-side integration
- **Lambda Function Name**: For monitoring and debugging

## API Usage

### Authentication

1. **User Registration/Login**: Use Cognito Hosted UI or integrate with your application
2. **Get Access Token**: From Cognito authentication flow
3. **API Calls**: Include `Authorization: Bearer <access_token>` header

### Search Endpoints

```bash
# GET request with query parameter
GET /search/sku?q=医療機器&size=20

# POST request with JSON body
POST /search/sku
{
  "query": "医療機器",
  "size": 20,
  "filters": {
    "category": "medicine"
  }
}
```

### Response Format

```json
{
  "query": "医療機器",
  "total_hits": 15,
  "max_score": 8.5,
  "results": [
    {
      "sku_code": "MED-001",
      "name": "医療機器A",
      "description": "高品質な医療機器",
      "category": "medicine",
      "price": 50000,
      "stock_status": "in_stock",
      "score": 8.5,
      "highlights": {
        "name": ["<mark>医療機器</mark>A"]
      }
    }
  ],
  "took": 12,
  "timed_out": false
}
```

## Monitoring and Logging

### CloudWatch Logs

- API Gateway logs: `/aws/apigateway/fuzzy-sku-{env}`
- Lambda logs: `/aws/lambda/fuzzy-sku-{env}-search-function`

### CloudWatch Metrics

- Lambda: Duration, Errors, Invocations, Throttles
- API Gateway: Count, Latency, 4XXError, 5XXError
- Cognito: SignInSuccesses, SignInFailures

### Production Monitoring

- CloudWatch Dashboard with key metrics
- Alarms for Lambda errors and API Gateway 5XX errors
- X-Ray tracing for performance analysis

## Security Features

### Network Security

- VPC configuration for Lambda (recommended for production)
- Security groups for network access control
- Private subnets for enhanced isolation

### Authentication & Authorization

- Cognito User Pool with advanced security features
- MFA support (SMS, TOTP)
- OAuth 2.0 / OIDC compliance
- JWT token validation

### Data Protection

- HTTPS only (TLS 1.2+)
- Encryption at rest and in transit
- IAM roles with least privilege principle
- Request validation and input sanitization

## Cost Optimization

### Staging Environment

- Lower Lambda memory allocation (512MB)
- Reduced reserved concurrency (5)
- Shorter log retention (14 days)
- Lower API Gateway throttling limits

### Production Environment

- Optimized Lambda memory allocation (1024MB)
- Higher reserved concurrency (20)
- Longer log retention (30 days)
- Higher API Gateway throttling limits

## Troubleshooting

### Common Issues

1. **Terraform Backend Error**

   - Ensure S3 bucket exists and is accessible
   - Check AWS credentials and permissions

2. **Lambda Deployment Fails**

   - Verify OpenSearch endpoint is accessible
   - Check IAM permissions for OpenSearch access

3. **API Gateway Authorization Fails**

   - Verify Cognito User Pool configuration
   - Check callback URLs match your application

4. **Search Returns No Results**
   - Verify OpenSearch index exists and has data
   - Check index name configuration
   - Review Lambda logs for errors

### Debug Commands

```bash
# Check Terraform state
terraform show

# View detailed logs
aws logs tail /aws/lambda/fuzzy-sku-{env}-search-function --follow

# Test Lambda function
aws lambda invoke --function-name fuzzy-sku-{env}-search-function \
  --payload '{"query":"test"}' response.json

# Test API Gateway
curl -X POST "https://{api-id}.execute-api.ap-northeast-3.amazonaws.com/v1/search/sku" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

## Next Steps

1. **Deploy OpenSearch Infrastructure**: If not already deployed
2. **Configure DNS and SSL**: Set up custom domain names
3. **Implement CI/CD Pipeline**: Automate deployments
4. **Set up Monitoring Alerts**: Configure SNS notifications
5. **Performance Testing**: Load test the API endpoints
6. **Security Audit**: Review and harden security settings

## Support

For issues and questions:

- Check CloudWatch logs for detailed error information
- Review Terraform plan before applying changes
- Test changes in staging before production deployment
- Maintain proper backup and rollback procedures
