# Environment Configuration

This frontend application requires the following environment variables to be set:

## Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# AWS Cognito Configuration
REACT_APP_AWS_REGION=ap-northeast-3
REACT_APP_USER_POOL_ID=your-user-pool-id
REACT_APP_USER_POOL_CLIENT_ID=your-client-id
REACT_APP_IDENTITY_POOL_ID=your-identity-pool-id

# API Configuration
REACT_APP_API_BASE_URL=your-api-gateway-url
```

## Configuration Details

- **REACT_APP_AWS_REGION**: AWS region where your Cognito and API Gateway are deployed
- **REACT_APP_USER_POOL_ID**: Cognito User Pool ID for authentication
- **REACT_APP_USER_POOL_CLIENT_ID**: Cognito User Pool Client ID for the application
- **REACT_APP_IDENTITY_POOL_ID**: Cognito Identity Pool ID for temporary credentials
- **REACT_APP_API_BASE_URL**: Base URL for the API Gateway endpoints

## Security Notes

- Never commit the `.env` file to version control
- Use different environment files for different environments (dev, staging, prod)
- Ensure all environment variables are prefixed with `REACT_APP_` to be available in the browser
