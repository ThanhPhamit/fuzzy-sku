# Fuzzy SKU Search - Authentication & Search Examples

## Setup Instructions

1. **Environment Configuration**
   Make sure your `.env` file contains:

   ```bash
   REACT_APP_AWS_REGION=ap-northeast-3
   REACT_APP_USER_POOL_ID=ap-northeast-3_2TsX1tIxD
   REACT_APP_USER_POOL_CLIENT_ID=51331lo6kcq9a2lu5r2undcpt6
   REACT_APP_IDENTITY_POOL_ID=your-identity-pool-id
   REACT_APP_API_BASE_URL=https://y9whah197h.execute-api.ap-northeast-3.amazonaws.com/v1
   ```

2. **Install Dependencies**

   ```bash
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

## Authentication Flow

### Login Process

1. Navigate to `/login`
2. Enter your Cognito username and password
3. The system will:
   - Authenticate with AWS Cognito
   - Store access token with expiration
   - Set up automatic token refresh
   - Redirect to search page

### Token Management

- Access tokens are automatically refreshed 5 minutes before expiration
- If refresh fails, user is automatically logged out
- Session state is persisted in localStorage (securely)

## Search API Examples

### Basic Search Request

```javascript
// Example: Search for "メイジバランスソフト"
GET /search/sku?q=メイジバランスソフト&size=15
Authorization: Bearer <access-token>
```

### Example Response

```json
{
  "hits": {
    "total": {
      "value": 42,
      "relation": "eq"
    },
    "hits": [
      {
        "_id": "12345",
        "_source": {
          "syohin_code": "MEI001",
          "syohin_name_1": "メイジバランスソフト",
          "syohin_name_2": "明治バランスソフト",
          "syohin_name_3": "Meiji Balance Soft"
        },
        "_score": 8.5
      }
    ]
  }
}
```

## Testing the API with cURL

### 1. First, get an access token by logging in through the UI

### 2. Test the search endpoint:

```bash
curl --location 'https://y9whah197h.execute-api.ap-northeast-3.amazonaws.com/v1/search/sku?q=メイジバランスソフト&size=15' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN_HERE'
```

### 3. Example with different search terms:

```bash
# Search for "ソフト" (soft)
curl --location 'https://y9whah197h.execute-api.ap-northeast-3.amazonaws.com/v1/search/sku?q=ソフト&size=10' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN_HERE'

# Search for "バランス" (balance)
curl --location 'https://y9whah197h.execute-api.ap-northeast-3.amazonaws.com/v1/search/sku?q=バランス&size=20' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN_HERE'
```

## Features

### Authentication Features

- ✅ Secure Cognito authentication
- ✅ Automatic token refresh
- ✅ Session persistence
- ✅ Automatic logout on token expiration
- ✅ Protected routes

### Search Features

- ✅ Fuzzy Japanese text search
- ✅ Multiple result sizes (10, 15, 25, 50)
- ✅ Search highlighting
- ✅ Responsive results display
- ✅ Error handling and retry logic
- ✅ Real-time search validation

### UI Features

- ✅ Modern responsive design
- ✅ Loading states and progress indicators
- ✅ Error message display
- ✅ Search result highlighting
- ✅ Mobile-friendly interface

## Troubleshooting

### Common Issues

1. **401 Unauthorized Error**

   - Token expired → Login again
   - Invalid credentials → Check username/password
   - Wrong user pool → Verify environment variables

2. **CORS Errors**

   - API Gateway CORS configuration
   - Check browser network tab for preflight requests

3. **Search Timeout**
   - Large result sets may take longer
   - Try reducing search size parameter

### Debug Mode

Enable debug logging by adding to your `.env`:

```bash
REACT_APP_DEBUG=true
```

This will show detailed authentication and API call logs in the browser console.
