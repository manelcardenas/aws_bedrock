# Authentication & Proxy Stack

This CDK stack provides authentication and API key protection for your existing AWS Bedrock APIs.

## 🏗️ Architecture

```
Frontend (S3) → Auth API Gateway → Auth Lambda (login)
                                 → Proxy Lambda → Existing Image API
                                                → Existing Text API
```

### What This Stack Does

1. **User Authentication**: Provides `/login` endpoint that validates credentials and returns JWT tokens
2. **API Key Protection**: Hides your existing API keys from the frontend by proxying requests
3. **User Management**: Stores user credentials in DynamoDB

### Key Components

- **DynamoDB Table**: Stores user credentials (username, password_hash, email)
- **Auth Lambda**: Handles login requests and generates JWT tokens
- **Proxy Lambda**: Validates JWTs and forwards requests to your existing APIs
- **API Gateway**: Exposes `/login`, `/proxy/image`, and `/proxy/text` endpoints

## 📋 Prerequisites

- AWS CLI configured with appropriate credentials
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.12+
- Your existing Image and Text API URLs and API keys

## 🚀 Deployment

### Step 1: Install Dependencies

```bash
cd infra_auth_stack
pip install -r requirements.txt
pip install -r services/requirements.txt
```

### Step 2: Configure Environment Variables

Before deploying, you need to configure the proxy Lambda with your existing API details:

Edit `infra_auth_stack/infra_auth_stack_stack.py` and update the `proxy_lambda` environment variables:

```python
environment={
    "JWT_SECRET": "CHANGE-THIS-TO-RANDOM-SECRET-IN-PRODUCTION",
    "IMAGE_API_URL": "https://your-actual-image-api.amazonaws.com/prod/image",
    "IMAGE_API_KEY": "your-actual-image-api-key",
    "TEXT_API_URL": "https://your-actual-text-api.amazonaws.com/prod/text",
    "TEXT_API_KEY": "your-actual-text-api-key",
}
```

**Important**: The JWT_SECRET in both `auth_lambda` and `proxy_lambda` must be identical!

### Step 3: Deploy the Stack

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy to development environment
cdk deploy --context env_name=dev

# Or deploy to production
cdk deploy --context env_name=prod
```

### Step 4: Get Stack Outputs

After deployment, note the following outputs:

- `UsersTableName`: The DynamoDB table name for users
- `LoginEndpoint`: Your new login URL
- `ImageProxyEndpoint`: Proxied image API endpoint
- `TextProxyEndpoint`: Proxied text API endpoint

## 👥 User Management

### Add a User

```bash
python manage_users.py add \
  --username john_doe \
  --password secret123 \
  --email john@example.com \
  --table-name dev-users-table-123456789012 \
  --region us-west-2
```

Replace `dev-users-table-123456789012` with your actual table name from the stack outputs.

### List All Users

```bash
python manage_users.py list \
  --table-name dev-users-table-123456789012 \
  --region us-west-2
```

### Delete a User

```bash
python manage_users.py delete \
  --username john_doe \
  --table-name dev-users-table-123456789012 \
  --region us-west-2
```

## 🔐 API Usage

### 1. Login to Get JWT Token

```bash
curl -X POST https://your-auth-api.amazonaws.com/prod/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secret123"
  }'
```

Response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "username": "john_doe",
  "expires_in": 86400
}
```

### 2. Generate Image (with JWT)

```bash
curl -X POST https://your-auth-api.amazonaws.com/prod/proxy/image \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "description": "A serene mountain landscape at sunset"
  }'
```

### 3. Summarize Text (with JWT)

```bash
curl -X POST "https://your-auth-api.amazonaws.com/prod/proxy/text?points=3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -d '{
    "text": "Your long text here..."
  }'
```

## 🔒 Security Best Practices

### Production Deployment

Before deploying to production:

1. **Use AWS Secrets Manager for JWT_SECRET**:

   ```python
   # Instead of hardcoding JWT_SECRET
   jwt_secret = secretsmanager.Secret(self, "JWTSecret",
       generate_secret_string=secretsmanager.SecretStringGenerator(
           secret_string_template='{}',
           generate_string_key='jwt_secret',
           exclude_punctuation=True,
       )
   )
   ```

2. **Store API Keys in Secrets Manager**:
   Don't hardcode API keys in the stack!

3. **Use bcrypt or argon2 for password hashing**:
   The current implementation uses SHA-256, which is not ideal for passwords.

4. **Enable API Gateway logging**:

   ```python
   api.deployment_stage.method_settings = {
       "/*/*": {
           "logging_level": aws_apigateway.MethodLoggingLevel.INFO,
           "data_trace_enabled": True
       }
   }
   ```

5. **Add rate limiting per user**:
   Currently, rate limiting is not implemented per user.

6. **Update CORS origins**:
   Change `allow_origins=["*"]` to your actual frontend domain.

## 🧪 Testing

### Test Login Endpoint

```bash
# Should succeed
curl -X POST https://your-api/prod/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"secret123"}'

# Should fail (invalid credentials)
curl -X POST https://your-api/prod/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"wrong"}'
```

### Test Proxy Endpoint

```bash
# Should fail (no token)
curl -X POST https://your-api/prod/proxy/image \
  -H "Content-Type: application/json" \
  -d '{"description":"test"}'

# Should succeed (with valid token)
curl -X POST https://your-api/prod/proxy/image \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"description":"test"}'
```

## 🐛 Troubleshooting

### "Invalid or expired token" Error

- Check that JWT_SECRET is identical in both auth_lambda and proxy_lambda
- Verify the token hasn't expired (default: 24 hours)
- Ensure you're including `Bearer` prefix in Authorization header

### "Backend configuration error" in Proxy

- Verify IMAGE_API_URL and IMAGE_API_KEY are set correctly
- Check CloudWatch logs for the proxy Lambda

### "Invalid credentials" on Login

- Verify the user exists in DynamoDB
- Check the password is correct
- Use `manage_users.py list` to see all users

### Deploy Fails with "Resource Already Exists"

- Run `cdk destroy` to clean up
- Or use a different env_name: `cdk deploy --context env_name=dev2`

## 📊 Monitoring

View Lambda logs:

```bash
# Auth Lambda logs
aws logs tail /aws/lambda/dev-auth-lambda-123456789012 --follow

# Proxy Lambda logs
aws logs tail /aws/lambda/dev-proxy-lambda-123456789012 --follow
```

## 🧹 Cleanup

To delete all resources:

```bash
cdk destroy --context env_name=dev
```

## 📝 Next Steps

1. ✅ Deploy this auth stack
2. ✅ Add test users to DynamoDB
3. ✅ Test login and proxy endpoints
4. 🔄 Update your frontend to use the new auth flow
5. 🔄 Remove hardcoded API keys from frontend

## 🤝 Integration with Frontend

Your frontend should now:

1. **Login Flow**:

   ```javascript
   const response = await fetch(`${AUTH_API_URL}/login`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ username, password }),
   });
   const { token } = await response.json();
   localStorage.setItem("jwt_token", token);
   ```

2. **API Calls**:
   ```javascript
   const token = localStorage.getItem("jwt_token");
   const response = await fetch(`${AUTH_API_URL}/proxy/image`, {
     method: "POST",
     headers: {
       "Content-Type": "application/json",
       Authorization: `Bearer ${token}`,
     },
     body: JSON.stringify({ description: "..." }),
   });
   ```

## 📄 License

MIT
