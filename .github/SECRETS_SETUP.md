# 🔐 GitHub Secrets Setup Guide

Quick reference for setting up GitHub Actions secrets.

## Required Secrets

### 1. AWS Credentials (All Workflows)

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
```

**How to get:**

1. Go to AWS Console → IAM → Users → Your user
2. Security credentials tab
3. Create access key → CLI
4. Copy both values

### 2. Auth Stack Secrets (deploy-auth.yml only)

#### JWT_SECRET

```bash
# Generate a secure random string
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### IMAGE_API_URL

```bash
# From your Image stack deployment
cd infra_images
cdk deploy --outputs-file outputs.json
cat outputs.json | grep ApiEndpoint
# Example: https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com/prod/
```

#### IMAGE_API_KEY

```bash
# Get the API key ID from stack outputs
cd infra_images
cdk deploy --outputs-file outputs.json
cat outputs.json | grep ApiKeyId
# Then get the actual key value:
aws apigateway get-api-key \
  --api-key <KEY_ID_FROM_OUTPUT> \
  --include-value \
  --region us-west-2 \
  --query 'value' \
  --output text
```

#### TEXT_API_URL

```bash
# From your Text stack deployment
cd infra
cdk deploy --outputs-file outputs.json
cat outputs.json | grep ApiEndpoint
# Example: https://xyz123.execute-api.eu-west-3.amazonaws.com/prod/
```

#### TEXT_API_KEY

```bash
# Get the API key ID from stack outputs
cd infra
cdk deploy --outputs-file outputs.json
cat outputs.json | grep ApiKeyId
# Then get the actual key value:
aws apigateway get-api-key \
  --api-key <KEY_ID_FROM_OUTPUT> \
  --include-value \
  --region eu-west-3 \
  --query 'value' \
  --output text
```

## Adding Secrets to GitHub

### Via Web Interface

1. Navigate to: `https://github.com/<YOUR_USERNAME>/aws_bedrock/settings/secrets/actions`
2. Click **"New repository secret"**
3. Enter secret name (exact match required!)
4. Paste secret value
5. Click **"Add secret"**

### Via GitHub CLI (gh)

```bash
# Install GitHub CLI
brew install gh  # macOS
# or download from https://cli.github.com/

# Authenticate
gh auth login

# Add secrets one by one
gh secret set AWS_ACCESS_KEY_ID --body "YOUR_ACCESS_KEY"
gh secret set AWS_SECRET_ACCESS_KEY --body "YOUR_SECRET_KEY"
gh secret set AWS_DEFAULT_REGION --body "us-east-1"

# Auth stack secrets
gh secret set JWT_SECRET --body "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
gh secret set IMAGE_API_URL --body "https://rtn0xug2ia.execute-api.us-west-2.amazonaws.com/prod/"
gh secret set IMAGE_API_KEY --body "YOUR_IMAGE_API_KEY"
gh secret set TEXT_API_URL --body "https://xyz123.execute-api.eu-west-3.amazonaws.com/prod/"
gh secret set TEXT_API_KEY --body "YOUR_TEXT_API_KEY"

# Verify secrets are set
gh secret list
```

## Verification Checklist

- [ ] `AWS_ACCESS_KEY_ID` set
- [ ] `AWS_SECRET_ACCESS_KEY` set
- [ ] `AWS_DEFAULT_REGION` set
- [ ] `JWT_SECRET` set (auth stack only)
- [ ] `IMAGE_API_URL` set (auth stack only)
- [ ] `IMAGE_API_KEY` set (auth stack only)
- [ ] `TEXT_API_URL` set (auth stack only)
- [ ] `TEXT_API_KEY` set (auth stack only)

## Testing

After setting secrets, test by:

1. Making a small change in `infra_auth_stack/README.md`
2. Commit and push to `main` branch
3. Go to Actions tab in GitHub
4. Watch "Deploy Auth & Proxy Infrastructure" workflow
5. Check for any "secret not set" errors

## Updating Secrets

If your API keys change:

```bash
# Update via CLI
gh secret set IMAGE_API_KEY --body "NEW_API_KEY_VALUE"

# Or via web interface (same steps as adding)
```

## Security Notes

⚠️ **Never**:

- Commit secrets to git
- Share secrets in chat/email
- Log secrets in application code
- Use same secrets for prod/dev

✅ **Always**:

- Rotate secrets regularly
- Use minimum required permissions
- Delete unused secrets
- Monitor secret usage in GitHub

---

For more details, see [README.md](README.md)
