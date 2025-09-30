# Quick Start Deployment Guide

## Prerequisites Setup

### 1. AWS Environment Setup

```bash
# Configure AWS CLI with MFA profile (matching your existing setup)
aws configure --profile welfan-lg-mfa
# Follow prompts to enter Access Key ID, Secret Access Key, Region (ap-northeast-3)

# Test AWS access
aws sts get-caller-identity --profile welfan-lg-mfa
```

### 2. Create Terraform State Storage

```bash
# Create S3 bucket for Terraform state (replace with your bucket name)
aws s3 mb s3://your-terraform-state-bucket-fuzzy-sku --region ap-northeast-3 --profile welfan-lg-mfa

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket-fuzzy-sku \
  --versioning-configuration Status=Enabled \
  --profile welfan-lg-mfa

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock-fuzzy-sku \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region ap-northeast-3 \
  --profile welfan-lg-mfa
```

## Configuration Updates

### 1. Update Backend Configuration

Edit these files to match your setup:

**infrastructure/environments/staging/providers.tf**:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket-fuzzy-sku"
  key            = "fuzzy-sku/staging/terraform.tfstate"
  region         = "ap-northeast-3"
  encrypt        = true
  dynamodb_table = "terraform-state-lock-fuzzy-sku"
  profile        = "welfan-lg-mfa"  # Add this line
}
```

**infrastructure/environments/production/providers.tf**:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket-fuzzy-sku"
  key            = "fuzzy-sku/production/terraform.tfstate"
  region         = "ap-northeast-3"
  encrypt        = true
  dynamodb_table = "terraform-state-lock-fuzzy-sku"
  profile        = "welfan-lg-mfa"  # Add this line
}
```

### 2. Update OpenSearch Endpoints

Replace the placeholder OpenSearch endpoints in:

**infrastructure/environments/staging/variables.tf**:

```hcl
variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
  default     = "https://search-fuzzy-sku-staging.ap-northeast-3.es.amazonaws.com"  # Update this
}
```

**infrastructure/environments/production/variables.tf**:

```hcl
variable "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
  default     = "https://search-fuzzy-sku-prod.ap-northeast-3.es.amazonaws.com"  # Update this
}
```

### 3. Update Callback URLs

Edit the callback URLs in the main.tf files for your actual domains:

**infrastructure/environments/staging/main.tf**:

```hcl
callback_urls = [
  "https://localhost:3000/callback",
  "https://staging.yourdomain.com/callback"  # Update this
]

logout_urls = [
  "https://localhost:3000/logout",
  "https://staging.yourdomain.com/logout"    # Update this
]
```

## Deployment Steps

### 1. Deploy Staging Environment

```bash
cd infrastructure
export AWS_PROFILE=welfan-lg-mfa

# Deploy staging
./deploy.sh staging
```

### 2. Test Staging Deployment

```bash
# Get the API endpoint URL
cd environments/staging
STAGING_API_URL=$(terraform output -raw api_gateway_url)
STAGING_SEARCH_URL=$(terraform output -raw search_endpoint_url)

echo "Staging API URL: $STAGING_API_URL"
echo "Staging Search URL: $STAGING_SEARCH_URL"

# Test the Lambda function directly (without auth)
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{"query":"test","size":10}' \
  --cli-binary-format raw-in-base64-out \
  --profile welfan-lg-mfa \
  response.json

cat response.json
```

### 3. Deploy Production Environment

```bash
# Deploy production (requires confirmation)
./deploy.sh production
```

## Post-Deployment Setup

### 1. Create Cognito Test Users

```bash
# For staging
USER_POOL_ID=$(cd environments/staging && terraform output -raw cognito_user_pool_id)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --user-attributes Name=email,Value=test@yourdomain.com \
  --temporary-password TempPass123! \
  --message-action SUPPRESS \
  --profile welfan-lg-mfa

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username testuser \
  --password SecurePass123! \
  --permanent \
  --profile welfan-lg-mfa
```

### 2. Test API with Authentication

```bash
# Get Cognito configuration
USER_POOL_ID=$(cd environments/staging && terraform output -raw cognito_user_pool_id)
CLIENT_ID=$(cd environments/staging && terraform output -raw cognito_user_pool_client_id)
LOGIN_URL=$(cd environments/staging && terraform output -raw cognito_login_url)

echo "User Pool ID: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
echo "Login URL: $LOGIN_URL"

# Use the login URL to authenticate and get access token
# Then test the API:
ACCESS_TOKEN="your_access_token_here"
SEARCH_URL=$(cd environments/staging && terraform output -raw search_endpoint_url)

curl -X POST "$SEARCH_URL" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"医療機器","size":10}'
```

## Monitoring Setup

### 1. Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/fuzzy-sku-staging-search-function --follow --profile welfan-lg-mfa

# View API Gateway logs
aws logs tail /aws/apigateway/fuzzy-sku-staging --follow --profile welfan-lg-mfa
```

### 2. Production Monitoring

Access the CloudWatch dashboard:

```bash
cd environments/production
DASHBOARD_URL=$(terraform output -raw cloudwatch_dashboard_url)
echo "Dashboard URL: $DASHBOARD_URL"
```

## Integration with Existing SKU Indexer

### 1. Update Your SKU Indexer for Lambda

Your existing `sku_indexer.py` can be adapted for the Lambda environment:

```python
# Add this to your sku_indexer.py for Lambda compatibility
import os

class JapaneseSKUIndexer:
    def __init__(self):
        # Use environment variables when running in Lambda
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            self.host = os.environ.get('OPENSEARCH_ENDPOINT')
            self.index_name = os.environ.get('INDEX_NAME', 'japanese_sku_index')
        else:
            # Your existing configuration for local development
            self.host = "your-opensearch-endpoint"
            self.index_name = "japanese_sku_index"

    # Your existing methods...
```

### 2. Update Lambda Function Template

Replace the Lambda function template with your optimized search logic:

```bash
# Copy your search logic to the Lambda template
cp fuzzy-sku-test/sku_indexer.py infrastructure/modules/lambda_search/templates/lambda_function.py

# Modify the template to include Lambda handler wrapper
# (Keep the existing lambda_handler function and add your class)
```

## Troubleshooting

### Common Issues

1. **Backend initialization fails**

   ```bash
   # Check if S3 bucket exists and is accessible
   aws s3 ls s3://your-terraform-state-bucket-fuzzy-sku --profile welfan-lg-mfa

   # Check DynamoDB table
   aws dynamodb describe-table --table-name terraform-state-lock-fuzzy-sku --profile welfan-lg-mfa
   ```

2. **Lambda function fails to connect to OpenSearch**

   ```bash
   # Check if OpenSearch endpoint is accessible
   curl -X GET "https://your-opensearch-endpoint/_cluster/health"

   # Check Lambda logs for connection errors
   aws logs filter-log-events \
     --log-group-name /aws/lambda/fuzzy-sku-staging-search-function \
     --filter-pattern "ERROR" \
     --profile welfan-lg-mfa
   ```

3. **API Gateway returns 403 Forbidden**
   ```bash
   # Check Cognito user pool configuration
   USER_POOL_ID=$(cd environments/staging && terraform output -raw cognito_user_pool_id)
   aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID --profile welfan-lg-mfa
   ```

### Rollback Procedure

```bash
# If deployment fails, rollback to previous state
cd infrastructure/environments/staging  # or production
terraform plan -destroy
terraform apply -destroy  # Only if necessary
```

## Security Best Practices

1. **Enable MFA for all users** in production Cognito User Pool
2. **Restrict CORS origins** to your actual domain names
3. **Use VPC configuration** for Lambda in production
4. **Enable AWS CloudTrail** for audit logging
5. **Implement WAF** for API Gateway protection
6. **Regular security audits** and dependency updates

## Performance Optimization

1. **Monitor Lambda metrics** and adjust memory allocation
2. **Configure reserved concurrency** based on expected load
3. **Implement caching** at API Gateway or application level
4. **Optimize OpenSearch queries** for better performance
5. **Use CloudFront CDN** for global distribution

## Next Steps

1. **Set up CI/CD pipeline** for automated deployments
2. **Implement automated testing** for infrastructure changes
3. **Configure monitoring alerts** for production issues
4. **Plan disaster recovery** procedures
5. **Document operational procedures** for your team

---

**Estimated Deployment Time**: 30-45 minutes for staging + production
**Required AWS Services**: Lambda, API Gateway, Cognito, CloudWatch, S3, DynamoDB
**Monthly Cost Estimate**: $50-100 for staging, $200-500 for production (depending on usage)
