# 🚀 Quick Start Guide - Auth Stack

## TL;DR - Deploy in 5 Steps

```bash
# 1. Navigate to auth stack
cd infra_auth_stack

# 2. Install dependencies
pip install -r requirements.txt
pip install -r services/requirements.txt

# 3. Update API URLs and Keys in infra_auth_stack_stack.py
# Edit lines 94-99 with your real API endpoints and keys

# 4. Deploy
cdk deploy --context env_name=dev

# 5. Add a test user
python manage_users.py add \
  --username testuser \
  --password test123 \
  --email test@example.com \
  --table-name <TABLE_NAME_FROM_OUTPUT> \
  --region <YOUR_REGION>
```

## 📝 What You Need Before Starting

1. Your **Image API URL** (from `infra_images` stack output)
2. Your **Image API Key** (get it with: `aws apigateway get-api-key --api-key <KEY_ID> --include-value`)
3. Your **Text API URL** (from `infra` stack output)
4. Your **Text API Key** (same process as above)

## 🔧 Configuration Steps

### 1. Update the Stack Configuration

Edit `infra_auth_stack/infra_auth_stack/infra_auth_stack_stack.py`:

**Line 72-77** - Update JWT_SECRET (both lambdas must match!):

```python
"JWT_SECRET": "YOUR-SUPER-SECRET-JWT-KEY-HERE",  # Generate a random 32+ character string
```

**Line 94-99** - Update API URLs and Keys:

```python
"IMAGE_API_URL": "https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com/prod/image",
"IMAGE_API_KEY": "your-actual-image-api-key-here",
"TEXT_API_URL": "https://t847x9nytb.execute-api.eu-west-3.amazonaws.com/prod/text",
"TEXT_API_KEY": "your-actual-text-api-key-here",
```

### 2. Generate a Secure JWT Secret

```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: OpenSSL
openssl rand -base64 32

# Option 3: Use this online (but generate your own in production!)
# https://www.uuidgenerator.net/
```

Copy the generated value and use it as `JWT_SECRET` in BOTH lambdas.

## 🧪 Testing After Deployment

### Test 1: Login

```bash
export AUTH_API="https://your-api-url.amazonaws.com/prod"

# Should return a JWT token
curl -X POST ${AUTH_API}/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123"
  }'
```

Expected response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "testuser",
  "expires_in": 86400
}
```

### Test 2: Use JWT to Generate Image

```bash
export JWT_TOKEN="<token-from-login-response>"

curl -X POST ${AUTH_API}/proxy/image \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "description": "A beautiful sunset over mountains"
  }'
```

### Test 3: Use JWT to Summarize Text

```bash
curl -X POST "${AUTH_API}/proxy/text?points=3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "text": "Your long text here to summarize..."
  }'
```

## 🐛 Common Issues

### Issue: "Invalid or expired token"

**Cause**: JWT_SECRET doesn't match between auth_lambda and proxy_lambda

**Fix**: Make sure both lambdas use the EXACT same JWT_SECRET

### Issue: "Backend configuration error"

**Cause**: Missing or incorrect API URLs/Keys in proxy_lambda

**Fix**:

1. Check CloudWatch logs: `aws logs tail /aws/lambda/dev-proxy-lambda-<account-id> --follow`
2. Verify IMAGE_API_URL, IMAGE_API_KEY, TEXT_API_URL, TEXT_API_KEY are set correctly

### Issue: Can't find table name

**Solution**: After deployment, run:

```bash
aws cloudformation describe-stacks \
  --stack-name InfraAuthStack-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UsersTableName`].OutputValue' \
  --output text
```

## 📊 View Logs

```bash
# Auth Lambda (login)
aws logs tail /aws/lambda/dev-auth-lambda-<account-id> --follow

# Proxy Lambda (image/text forwarding)
aws logs tail /aws/lambda/dev-proxy-lambda-<account-id> --follow
```

## 🎯 Architecture Flow

```
1. User visits frontend (S3 website)
2. User enters username/password
3. Frontend → POST /login → Auth Lambda
4. Auth Lambda checks DynamoDB → Returns JWT token
5. Frontend stores JWT in localStorage
6. User clicks "Generate Image"
7. Frontend → POST /proxy/image + JWT → Proxy Lambda
8. Proxy Lambda validates JWT
9. Proxy Lambda adds x-api-key header
10. Proxy Lambda → Your existing Image API
11. Image API processes request
12. Response flows back to frontend
```

## ✅ Success Checklist

Before considering deployment complete:

- [ ] JWT_SECRET is set and matches in both lambdas
- [ ] IMAGE_API_URL and IMAGE_API_KEY are correct
- [ ] TEXT_API_URL and TEXT_API_KEY are correct
- [ ] Stack deployed successfully
- [ ] At least one test user added to DynamoDB
- [ ] Login endpoint tested and returns JWT token
- [ ] Proxy endpoints tested with JWT token
- [ ] CloudWatch logs show no errors

## 🔄 Update Frontend

After auth stack is working, update your frontend `config.js`:

```javascript
const CONFIG = {
  // NEW: Auth API (replaces direct API calls)
  AUTH_API_URL: "https://your-auth-api.amazonaws.com/prod",

  // OLD: Remove these (now handled by proxy)
  // TEXT_API_URL: "...",
  // IMAGE_API_URL: "...",
  // API_KEY: ""
};
```

Update your frontend to:

1. Show login form first
2. Store JWT token after login
3. Use `/proxy/image` and `/proxy/text` endpoints
4. Include JWT in `Authorization: Bearer <token>` header

## 📞 Need Help?

Check the full documentation in `README_DEPLOYMENT.md` for detailed explanations.
