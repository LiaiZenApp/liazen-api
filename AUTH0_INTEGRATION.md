# Auth0 Integration Guide

This guide explains how to set up and test the Auth0 integration with the FastAPI application.

## Prerequisites

1. Python 3.8+
2. pip (Python package manager)
3. An Auth0 account and application
4. The `.env.test` file with your Auth0 credentials

## Setup

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure your `.env.test` file is properly configured with your Auth0 credentials:
   ```
   AUTH0_DOMAIN=your-auth0-domain
   AUTH0_CLIENT_ID=your-client-id
   AUTH0_CLIENT_SECRET=your-client-secret
   AUTH0_AUDIENCE=your-audience
   ```

## Testing the Integration

### Running the FastAPI Server

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000`

### Testing the Auth0 Integration

Run the test script to verify the Auth0 integration:

```bash
python scripts/test_auth0_integration.py
```

This script will:
1. Test the public endpoint (no authentication required)
2. Test the metadata endpoint
3. Get an access token from Auth0
4. Test the protected endpoint with the access token

### Manual Testing

You can also test the endpoints manually:

1. **Public Endpoint** (no authentication required):
   ```
   GET /api/auth0-test/public
   ```

2. **Metadata Endpoint** (no authentication required):
   ```
   GET /api/auth0-test/metadata
   ```

3. **Protected Endpoint** (requires authentication):
   ```
   GET /api/auth0-test/protected
   Authorization: Bearer YOUR_AUTH0_TOKEN
   ```

## Troubleshooting

### Common Issues

1. **Invalid Token Errors**:
   - Make sure your Auth0 credentials in `.env.test` are correct
   - Verify that the token audience matches your API identifier in Auth0
   - Check that the token hasn't expired

2. **CORS Issues**:
   - Make sure your Auth0 application's allowed origins include `http://localhost:8000`
   - Check the CORS configuration in `main.py`

3. **Rate Limiting**:
   - If you're making too many requests, you might hit Auth0's rate limits
   - Implement proper error handling and retry logic in your application

## Next Steps

1. Implement user registration and login flows
2. Set up role-based access control (RBAC)
3. Add refresh token handling
4. Implement token revocation
5. Set up proper logging and monitoring

## Security Considerations

- Never commit your `.env` or `.env.test` files to version control
- Use environment variables for sensitive information
- Implement proper error handling for authentication failures
- Set appropriate token expiration times
- Use HTTPS in production
- Regularly rotate your Auth0 client secrets
