# 🏗️ Complete Authentication Architecture

## High-Level Flow

```
┌─────────────┐
│   Browser   │ (User enters username/password)
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. POST /login {username, password}
       │ (No authentication required)
       ▼
┌────────────────────────────────────────────────────────────┐
│            🌐 API Gateway (Auth Stack)                     │
│   https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com  │
│                                                            │
│   Routes:                                                  │
│   • POST /login         → Auth Lambda (public)            │
│   • POST /proxy/image   → Proxy Lambda (JWT required)     │
│   • POST /proxy/text    → Proxy Lambda (JWT required)     │
└────────────┬──────────────────────────────────────────────┘
             │
             │ 2. Invokes Lambda
             ▼
┌──────────────────────────────────────────────────────────────┐
│       📦 Lambda: prod-auth-lambda-969341425463              │
│       Handler: auth.login_handler                            │
│                                                              │
│   Logic:                                                     │
│   1. Extract username/password from request body            │
│   2. Query DynamoDB for user                                │
│   3. Verify password hash (SHA-256)                         │
│   4. Generate JWT token (signed with JWT_SECRET)            │
│   5. Return token + username + expiration                   │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 3. Get user from table
             ▼
┌──────────────────────────────────────────────────────────────┐
│       🗄️ DynamoDB: prod-users-table-969341425463           │
│                                                              │
│   Schema:                                                    │
│   • username (PK)        - String                           │
│   • password_hash        - String (SHA-256)                 │
│   • email                - String                           │
│   • created_at           - ISO DateTime                     │
│                                                              │
│   Example:                                                   │
│   {                                                          │
│     "username": "manel",                                     │
│     "password_hash": "5e884898da28047151d0e56f8dc6292773...",│
│     "email": "manel@sam.com",                               │
│     "created_at": "2025-11-12T09:15:23.456Z"                │
│   }                                                          │
└──────────────────────────────────────────────────────────────┘
             │
             │ 4. Return user data
             ▼
      (Back to Auth Lambda)
             │
             │ 5. Response with JWT
             ▼
┌─────────────────────────────────────────────────────────────┐
│   Browser receives:                                         │
│   {                                                         │
│     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",   │
│     "username": "manel",                                    │
│     "expires_in": 86400                                     │
│   }                                                         │
│                                                             │
│   → Store token in localStorage                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Image Generation Flow (Protected)

```
┌─────────────┐
│   Browser   │ (User clicks "Generate Image")
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. POST /proxy/image
       │    Headers: Authorization: Bearer eyJhbGci...
       │    Body: { "description": "A sunset..." }
       ▼
┌────────────────────────────────────────────────────────────┐
│            🌐 API Gateway (Auth Stack)                     │
│   https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com  │
└────────────┬──────────────────────────────────────────────┘
             │
             │ 2. Invokes Lambda with event
             ▼
┌──────────────────────────────────────────────────────────────┐
│       📦 Lambda: prod-proxy-lambda-969341425463             │
│       Handler: auth.proxy_handler                            │
│                                                              │
│   Logic:                                                     │
│   1. Extract JWT from Authorization header                  │
│   2. Validate JWT signature (using JWT_SECRET)              │
│   3. Check expiration (must be < 24 hours old)             │
│   4. Determine target API from path (/proxy/image)         │
│   5. Get IMAGE_API_URL and IMAGE_API_KEY from env vars     │
│   6. Forward request to existing Image API                  │
│                                                              │
│   Environment Variables:                                     │
│   • JWT_SECRET          - "8hF3k9Lm2nP5qR7t..."           │
│   • IMAGE_API_URL       - "https://rtn0xug2ia..."         │
│   • IMAGE_API_KEY       - "owIAkcnmwK..." (HIDDEN!)       │
│   • TEXT_API_URL        - "https://xyz123..."             │
│   • TEXT_API_KEY        - "jlOZQ83k1U..." (HIDDEN!)       │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 3. HTTP POST with API key
             │    Headers: x-api-key: owIAkcnmwK...
             │    Body: { "description": "A sunset..." }
             ▼
┌────────────────────────────────────────────────────────────┐
│     🌐 API Gateway (Image Stack - us-west-2)              │
│   https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com  │
│                                                            │
│   Validates: x-api-key header                             │
└────────────┬──────────────────────────────────────────────┘
             │
             │ 4. Invokes Lambda
             ▼
┌──────────────────────────────────────────────────────────────┐
│       📦 Lambda: prod-image-generation-lambda               │
│       Handler: image.handler                                 │
│                                                              │
│   Logic:                                                     │
│   1. Extract description from request                       │
│   2. Call Amazon Bedrock (Titan Image Generator)           │
│   3. Generate image                                         │
│   4. Upload to S3 bucket                                    │
│   5. Create pre-signed URL (valid 1 hour)                  │
│   6. Return URL to caller                                   │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 5. Invoke Bedrock Model
             ▼
┌──────────────────────────────────────────────────────────────┐
│       🤖 Amazon Bedrock                                      │
│       Model: amazon.titan-image-generator-v1                 │
│                                                              │
│   Input: Text description                                    │
│   Output: Base64 encoded image                              │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 6. Return generated image
             ▼
      (Back to Image Lambda)
             │
             │ 7. Upload to S3
             ▼
┌──────────────────────────────────────────────────────────────┐
│       📂 S3 Bucket: prod-image-generation-bucket            │
│                                                              │
│   • CORS enabled (allows browser access)                    │
│   • Lifecycle: auto-delete after 30 days                   │
│   • Block public access (use pre-signed URLs)              │
└──────────────────────────────────────────────────────────────┘
             │
             │ 8. Response with pre-signed URL
             ▼
      (Back through all layers)
             │
             │ 9. Final response
             ▼
┌─────────────────────────────────────────────────────────────┐
│   Browser receives:                                         │
│   {                                                         │
│     "image_url": "https://prod-image-generation-bucket...  │
│                   ?X-Amz-Signature=...",                   │
│     "description": "A sunset...",                          │
│     "created_at": "2025-11-12T10:27:13Z"                   │
│   }                                                         │
│                                                             │
│   → Display image in <img> tag                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Text Summary Flow (Protected)

```
┌─────────────┐
│   Browser   │ (User clicks "Summarize")
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. POST /proxy/text?points=3
       │    Headers: Authorization: Bearer eyJhbGci...
       │    Body: { "text": "Long text here..." }
       ▼
┌────────────────────────────────────────────────────────────┐
│            🌐 API Gateway (Auth Stack)                     │
│   https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com  │
└────────────┬──────────────────────────────────────────────┘
             │
             │ 2. Invokes Lambda
             ▼
┌──────────────────────────────────────────────────────────────┐
│       📦 Lambda: prod-proxy-lambda-969341425463             │
│       Handler: auth.proxy_handler                            │
│                                                              │
│   Logic: (same as image flow)                               │
│   1. Validate JWT                                           │
│   2. Extract query params (?points=3)                       │
│   3. Get TEXT_API_URL and TEXT_API_KEY                      │
│   4. Forward to Text API with API key                       │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 3. HTTP POST with API key
             │    Headers: x-api-key: jlOZQ83k1U...
             │    Query: ?points=3
             │    Body: { "text": "Long text..." }
             ▼
┌────────────────────────────────────────────────────────────┐
│     🌐 API Gateway (Text Stack - eu-west-3)               │
│   https://xyz123.execute-api.eu-west-3.amazonaws.com      │
│                                                            │
│   Validates:                                               │
│   • x-api-key header                                      │
│   • Query parameter: points (required)                    │
│   • Body: text field (1-5000 chars)                       │
└────────────┬──────────────────────────────────────────────┘
             │
             │ 4. Invokes Lambda
             ▼
┌──────────────────────────────────────────────────────────────┐
│       📦 Lambda: prod-text-summary-lambda                   │
│       Handler: summary.handler                               │
│                                                              │
│   Logic:                                                     │
│   1. Extract text and points from request                   │
│   2. Call Amazon Bedrock (Titan Text Express)              │
│   3. Generate summary with N bullet points                  │
│   4. Return summary to caller                               │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 5. Invoke Bedrock Model
             ▼
┌──────────────────────────────────────────────────────────────┐
│       🤖 Amazon Bedrock                                      │
│       Model: amazon.titan-text-express-v1                    │
│                                                              │
│   Input: Prompt + text to summarize                         │
│   Output: Summary in bullet points                          │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ 6. Return summary
             ▼
      (Back through all layers)
             │
             │ 7. Final response
             ▼
┌─────────────────────────────────────────────────────────────┐
│   Browser receives:                                         │
│   {                                                         │
│     "summary": "• Point 1\n• Point 2\n• Point 3",          │
│     "original_length": 1234,                                │
│     "summary_length": 156                                   │
│   }                                                         │
│                                                             │
│   → Display summary in <div>                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Model

### What the User Can See (Browser DevTools)

```javascript
// ✅ User can see JWT token (but it's temporary!)
localStorage.getItem("jwt_token");
// → "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6Im1hbmVsIi..."

// ✅ User can see requests in Network tab
fetch("https://oa2psn63h1.../proxy/image", {
  headers: {
    Authorization: "Bearer eyJhbGci...", // Visible but expires!
  },
});
```

### What the User CANNOT See (Hidden in Lambda)

```python
# ❌ API keys are hidden in Lambda environment variables
# User NEVER sees these in browser!
IMAGE_API_KEY = "owIAkcnmwK..."  # Hidden in Lambda!
TEXT_API_KEY = "jlOZQ83k1U..."   # Hidden in Lambda!
JWT_SECRET = "8hF3k9Lm2nP5..."   # Used to sign/verify tokens
```

### Security Benefits

1. **JWT Tokens Expire** (24 hours)

   - Even if stolen, token becomes useless after expiration
   - User must login again

2. **API Keys Hidden**

   - Never sent to browser
   - Stored securely in Lambda environment
   - Only accessible by AWS IAM role

3. **User-Specific Access**

   - Each JWT is tied to a username
   - Can add per-user rate limiting later
   - Can revoke specific users

4. **Request Validation**
   - JWT signature verified on every request
   - Tampered tokens rejected immediately

---

## AWS Services Used

| Service                 | Purpose                        | Region                | Cost                         |
| ----------------------- | ------------------------------ | --------------------- | ---------------------------- |
| **DynamoDB**            | Store user credentials         | eu-west-3             | Pay-per-request (~$0)        |
| **Lambda (Auth)**       | Validate login, generate JWT   | eu-west-3             | Per-invocation (~$0)         |
| **Lambda (Proxy)**      | Validate JWT, forward requests | eu-west-3             | Per-invocation (~$0)         |
| **API Gateway (Auth)**  | Public endpoints for auth      | eu-west-3             | Per-request (~$3.50/million) |
| **Lambda (Image)**      | Generate images via Bedrock    | us-west-2             | Per-invocation               |
| **Lambda (Text)**       | Summarize text via Bedrock     | eu-west-3             | Per-invocation               |
| **API Gateway (Image)** | Protected image endpoint       | us-west-2             | Per-request                  |
| **API Gateway (Text)**  | Protected text endpoint        | eu-west-3             | Per-request                  |
| **S3**                  | Store generated images         | us-west-2             | Storage + transfer           |
| **Bedrock**             | AI image & text generation     | us-west-2 & eu-west-3 | Per-token/image              |

---

## Request Parameters Reference

### Login Request

```json
POST https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com/prod/login

Headers:
  Content-Type: application/json

Body:
{
  "username": "manel",
  "password": "martina"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "manel",
  "expires_in": 86400
}
```

### Image Generation Request

```json
POST https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com/prod/proxy/image

Headers:
  Content-Type: application/json
  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Body:
{
  "description": "A beautiful sunset over mountains with snow"
}

Response:
{
  "image_url": "https://prod-image-generation-bucket-969341425463.s3...",
  "description": "A beautiful sunset over mountains with snow",
  "created_at": "2025-11-12T10:27:13Z"
}
```

### Text Summary Request

```json
POST https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com/prod/proxy/text?points=3

Headers:
  Content-Type: application/json
  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Body:
{
  "text": "Your long text here to summarize..."
}

Response:
{
  "summary": "• First key point\n• Second key point\n• Third key point",
  "original_length": 1234,
  "summary_length": 156
}
```

---

## Environment Variables

### Auth Lambda (`prod-auth-lambda-969341425463`)

```bash
USERS_TABLE=prod-users-table-969341425463
JWT_SECRET=8hF3k9Lm2nP5qR7tV0wX1yZ4aB6cD8eF9gH2jK4lM6n
JWT_EXPIRATION_HOURS=24
LOG_LEVEL=INFO
```

### Proxy Lambda (`prod-proxy-lambda-969341425463`)

```bash
JWT_SECRET=8hF3k9Lm2nP5qR7tV0wX1yZ4aB6cD8eF9gH2jK4lM6n  # Must match Auth Lambda!
IMAGE_API_URL=https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com/prod/image
IMAGE_API_KEY=owIAkcnmwK...
TEXT_API_URL=https://xyz123.execute-api.eu-west-3.amazonaws.com/prod/text
TEXT_API_KEY=jlOZQ83k1U...
LOG_LEVEL=INFO
```

---

## IAM Roles & Permissions

### Auth Lambda Role

- **DynamoDB**: `dynamodb:GetItem` on users table
- **CloudWatch Logs**: Write logs

### Proxy Lambda Role

- **CloudWatch Logs**: Write logs
- **No AWS service access** (calls external APIs via HTTP)

### Image Lambda Role

- **Bedrock**: `bedrock:InvokeModel` on Titan Image Generator
- **S3**: `s3:PutObject`, `s3:GetObject` on image bucket
- **CloudWatch Logs**: Write logs

### Text Lambda Role

- **Bedrock**: `bedrock:InvokeModel` on Titan Text Express
- **CloudWatch Logs**: Write logs
