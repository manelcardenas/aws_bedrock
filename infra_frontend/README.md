# Frontend Infrastructure

This CDK stack deploys the Bedrock Playground frontend to AWS using:

- **S3** for static file hosting
- **CloudFront** as CDN for global delivery with HTTPS

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9+
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Deployment

### Deploy to Development

```bash
cdk deploy --context env_name=dev
```

### Deploy to Production

```bash
cdk deploy --context env_name=prod
```

## After Deployment

After deploying, you'll receive outputs including:

- **WebsiteURL**: The CloudFront URL where your frontend is accessible (e.g., https://d1234567890.cloudfront.net)
- **DistributionId**: CloudFront distribution ID for cache invalidation
- **WebsiteBucketName**: S3 bucket name where files are stored

### Configure Authentication

The frontend now uses JWT-based authentication through the auth proxy Lambda:

1. **Update the auth API URL** in `src/frontend/js/config.js`:

   ```javascript
   AUTH_API_URL: "https://your-auth-api-id.execute-api.eu-west-3.amazonaws.com/prod";
   ```

   Get this URL from your `infra_auth_stack` deployment outputs.

2. **Create users** using the management script:

   ```bash
   cd infra_auth_stack
   python manage_users.py add username password
   ```

3. **Access the website** at the CloudFront URL and login with your credentials

**Note**: The frontend no longer requires direct API keys or endpoints. All API calls go through the authenticated proxy Lambda which handles:

- JWT token validation
- Adding API keys to backend requests
- Routing to the correct backend APIs (text summary and image generation)

## Updating the Frontend

After making changes to files in `src/frontend/`:

1. Re-deploy the stack:

```bash
cdk deploy --context env_name=dev
```

The deployment will automatically:

- Upload new files to S3
- Invalidate CloudFront cache
- Make changes live within a few minutes

## Useful Commands

- `cdk ls` - List all stacks
- `cdk synth` - Synthesize CloudFormation template
- `cdk diff` - Compare deployed stack with current state
- `cdk deploy` - Deploy stack
- `cdk destroy` - Destroy stack

## Cache Invalidation

If you need to manually invalidate CloudFront cache:

```bash
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Architecture

```
User → CloudFront (CDN) → S3 (Static Files: login.html, index.html, JS, CSS)
              ↓
      Login with username/password
              ↓
    Auth Lambda (validates credentials, returns JWT token)
              ↓
  User stores JWT token, accesses main app
              ↓
    Proxy Lambda (validates JWT, adds API keys)
         ↙          ↘
Text Summary API   Image Generation API
```

## Security Features

- **JWT Authentication** - User login required before accessing the app
- **Token Validation** - Backend proxy validates JWT on every API call
- **No Exposed API Keys** - API keys hidden in Lambda, never sent to browser
- **HTTPS only** - CloudFront enforces HTTPS
- **Private S3** - Bucket is not publicly accessible
- **Origin Access Identity** - CloudFront uses OAI to access S3
- **Security headers** - HSTS, XSS protection, frame options, etc.
- **CORS configured** - For API calls to backend services

## Cost Optimization

- Development environment uses fewer CloudFront edge locations
- Auto-deletion of S3 bucket in dev (retained in prod)
- Efficient caching policies to reduce origin requests
- Compressed assets for faster delivery
