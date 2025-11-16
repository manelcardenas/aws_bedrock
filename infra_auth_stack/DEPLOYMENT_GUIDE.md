# 🚀 Auth Stack Deployment - Step by Step

## Prerequisites

Before deploying the auth stack, you need:

1. ✅ Your **Image API** already deployed (`infra_images` stack)
2. ✅ Your **Text API** already deployed (`infra` stack)
3. ✅ The API URLs and API Keys from both stacks

## Step 1: Get Your Existing API Information

### Get Image API Details

```bash
# From your infra_images stack outputs
cd /Users/manel/Documents/zth/bedrock/infra_images
cdk deploy --outputs-file outputs.json

# Note the ApiEndpoint and ApiKeyId from the output
# Example: https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com/prod/

# Get the actual API key value
aws apigateway get-api-key \
  --api-key <YOUR_IMAGE_API_KEY_ID> \
  --include-value \
  --region us-west-2 \
  --query 'value' \
  --output text
```

### Get Text API Details

```bash
# From your infra stack outputs
cd /Users/manel/Documents/zth/bedrock/infra
cdk deploy --outputs-file outputs.json

# Note the ApiEndpoint and ApiKeyId from the output
# Example: https://xyz123.execute-api.eu-west-3.amazonaws.com/prod/

# Get the actual API key value
aws apigateway get-api-key \
  --api-key <YOUR_TEXT_API_KEY_ID> \
  --include-value \
  --region eu-west-3 \
  --query 'value' \
  --output text
```

## Step 2: Configure the Auth Stack

### 2.1 Generate a JWT Secret

```bash
# Generate a secure random string for JWT signing
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output: 8hF3k9Lm2nP5qR7tV0wX1yZ4aB6cD8eF9gH2jK4lM6n
```

### 2.2 Create .env File

```bash
cd /Users/manel/Documents/zth/bedrock/infra_auth_stack

# Copy the example file
cp .env.example .env

# Edit the .env file with your values
nano .env  # or use your preferred editor
```

Your `.env` file should look like this:

```bash
# JWT Configuration
JWT_SECRET=8hF3k9Lm2nP5qR7tV0wX1yZ4aB6cD8eF9gH2jK4lM6n  # Your generated secret
JWT_EXPIRATION_HOURS=24

# Image API (from infra_images stack)
IMAGE_API_URL=https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com/prod/image
IMAGE_API_KEY=abc123xyz789...  # Your actual image API key

# Text API (from infra stack)
TEXT_API_URL=https://xyz123.execute-api.eu-west-3.amazonaws.com/prod/text
TEXT_API_KEY=def456uvw012...  # Your actual text API key
```

### 2.3 Verify Configuration

```bash
# Check that .env is loaded correctly
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('JWT_SECRET:', os.getenv('JWT_SECRET')[:10] + '...')"
```

## Step 3: Install Dependencies

```bash
cd /Users/manel/Documents/zth/bedrock/infra_auth_stack

# Install CDK dependencies
pip install -r requirements.txt

# Install Lambda dependencies
pip install -r services/requirements.txt
```

## Step 4: Deploy the Stack

```bash
# Bootstrap CDK (if you haven't already)
cdk bootstrap aws://ACCOUNT-ID/eu-west-3

# Synthesize the CloudFormation template (optional, to verify)
cdk synth

# Deploy the stack
cdk deploy

# Confirm when prompted
```

**Expected output:**

```
✅  InfraAuthStack

Outputs:
InfraAuthStack.UsersTableName = prod-users-table-123456789012
InfraAuthStack.ApiEndpoint = https://abc123xyz.execute-api.eu-west-3.amazonaws.com/prod/
InfraAuthStack.LoginEndpoint = https://abc123xyz.execute-api.eu-west-3.amazonaws.com/prod/login
InfraAuthStack.ImageProxyEndpoint = https://abc123xyz.execute-api.eu-west-3.amazonaws.com/prod/proxy/image
InfraAuthStack.TextProxyEndpoint = https://abc123xyz.execute-api.eu-west-3.amazonaws.com/prod/proxy/text
```

**Save these outputs! You'll need them for:**

1. Adding users to DynamoDB
2. Updating your frontend configuration

## Step 5: Add Test Users

```bash
# Add a test user
python3 manage_users.py add \
  --username testuser \
  --password test123 \
  --email test@example.com \
  --table-name prod-users-table-123456789012 \
  --region eu-west-3

# List all users to verify
python3 manage_users.py list \
  --table-name prod-users-table-123456789012 \
  --region eu-west-3
```

## Step 6: Test the Deployment

### Test 1: Login

```bash
export AUTH_API="https://abc123xyz.execute-api.eu-west-3.amazonaws.com/prod"

# Should return a JWT token
curl -X POST ${AUTH_API}/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123"
  }'
```

**Expected response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "testuser",
  "expires_in": 86400
}
```

### Test 2: Generate Image with JWT

```bash
# Copy the token from the login response
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIs..."

curl -X POST ${AUTH_API}/proxy/image \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "description": "A beautiful sunset over mountains"
  }'
```

### Test 3: Summarize Text with JWT

```bash
curl -X POST "${AUTH_API}/proxy/text?points=3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "text": "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans."
  }'
```

## Troubleshooting

### Issue: "Import 'dotenv' could not be resolved"

```bash
pip install python-dotenv
```

### Issue: "Invalid credentials" when logging in

Check if the user exists:

```bash
python3 manage_users.py list --table-name prod-users-table-123456789012 --region eu-west-3
```

### Issue: "Backend configuration error" in proxy

This means your .env variables weren't loaded. Verify:

```bash
cat .env
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('IMAGE_API_URL'))"
```

### Issue: "Invalid or expired token"

- JWT_SECRET must be the same in both lambdas
- Check CloudWatch logs:

```bash
aws logs tail /aws/lambda/prod-auth-lambda-123456789012 --follow --region eu-west-3
aws logs tail /aws/lambda/prod-proxy-lambda-123456789012 --follow --region eu-west-3
```

## Summary of Resources Created

After deployment, you'll have:

1. **DynamoDB Table**: `prod-users-table-123456789012`
   - Stores user credentials
   - Pay-per-request billing
2. **Auth Lambda**: `prod-auth-lambda-123456789012`

   - Handles `/login` endpoint
   - Validates credentials
   - Returns JWT tokens

3. **Proxy Lambda**: `prod-proxy-lambda-123456789012`

   - Validates JWT tokens
   - Forwards requests to existing APIs
   - Hides API keys from frontend

4. **API Gateway**: `https://abc123xyz.execute-api.eu-west-3.amazonaws.com/prod/`
   - `/login` - Public endpoint (no auth)
   - `/proxy/image` - Protected (requires JWT)
   - `/proxy/text` - Protected (requires JWT)

## Next Steps

1. ✅ Update your frontend to use the new auth endpoints
2. ✅ Add login form to your HTML
3. ✅ Store JWT token in localStorage
4. ✅ Remove hardcoded API keys from frontend config
5. ✅ Use `/proxy/image` and `/proxy/text` instead of direct API calls

## Cleanup (if needed)

```bash
# To delete all resources
cdk destroy

# Confirm when prompted
```

This will remove:

- API Gateway
- Lambda functions
- DynamoDB table (and all users!)
- All associated IAM roles

---

**Note**: The region is set to `eu-west-3` in `app.py`. The DynamoDB table name is automatically generated as `prod-users-table-{account_id}`.
