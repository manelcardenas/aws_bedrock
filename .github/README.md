# 🤖 GitHub Actions CI/CD Documentation

Automated deployment workflows for AWS Bedrock infrastructure using GitHub Actions.

## 📋 Overview

This repository uses **GitHub Actions** to automatically deploy infrastructure changes to AWS when code is pushed to the `main` branch. Each stack has its own isolated workflow that only triggers when relevant files change.

## 🏗️ Architecture

```
GitHub Push → GitHub Actions → AWS CDK → AWS CloudFormation → AWS Services
```

### Deployment Flow

1. **Developer** pushes code to `main` branch
2. **GitHub Actions** detects file changes in specific directories
3. **Workflow** executes deployment steps (setup, build, deploy)
4. **AWS CDK** synthesizes CloudFormation templates
5. **CloudFormation** updates AWS resources
6. **Workflow** reports success/failure

## 📁 Workflow Files

### 1. `deploy.yml` - Image Generation Stack

**Purpose**: Deploys image generation infrastructure (Bedrock + S3 + Lambda)

**Trigger**: Changes to `infra_images/**`

**What it deploys**:

- Lambda function for image generation
- S3 bucket for storing images
- API Gateway endpoint
- Bedrock model invocation permissions

**Region**: `us-west-2`

**Stack Name**: `InfraImagesStack`

**Key Features**:

- ✅ Automatic CDK bootstrap check
- ✅ Stack backup before deployment
- ✅ Deployment preview (cdk diff)
- ✅ Automatic rollback on failure

---

### 2. `deploy-text-summary.yml` - Text Summary Stack

**Purpose**: Deploys text summarization infrastructure (Bedrock + Lambda)

**Trigger**: Changes to `infra/**`

**What it deploys**:

- Lambda function for text summarization
- API Gateway endpoint
- Bedrock model invocation permissions

**Region**: `eu-west-3`

**Stack Name**: `InfraStack`

**Key Features**:

- ✅ Deployment preview (cdk diff)
- ✅ Stack backup before deployment
- ✅ Automatic rollback on failure

---

### 3. `deploy-frontend.yml` - Frontend Stack

**Purpose**: Deploys static website infrastructure (S3 + CloudFront)

**Trigger**: Changes to `infra_frontend/**` or `src/frontend/**`

**What it deploys**:

- S3 bucket for static website hosting
- CloudFront CDN distribution
- Static HTML/CSS/JS files
- SSL certificate configuration

**Region**: Configurable via `AWS_DEFAULT_REGION` secret

**Stack Name**: `prod-FrontendStack`

**Key Features**:

- ✅ CloudFront cache invalidation
- ✅ Automatic static file upload
- ✅ Stack backup before deployment
- ✅ Deployment preview (cdk diff)

---

### 4. `deploy-auth.yml` - Authentication & Proxy Stack ⭐ NEW

**Purpose**: Deploys authentication and API proxy infrastructure

**Trigger**: Changes to `infra_auth_stack/**`

**What it deploys**:

- DynamoDB table for user credentials
- Auth Lambda (login handler)
- Proxy Lambda (API key protection)
- API Gateway endpoints (/login, /proxy/\*)

**Region**: `eu-west-3`

**Stack Name**: `InfraAuthStack`

**Key Features**:

- ✅ Environment variable validation
- ✅ Docker-based Lambda bundling
- ✅ CDK bootstrap check
- ✅ Stack backup before deployment
- ✅ Deployment preview (cdk diff)

**Special Requirements**:

- Requires 5 GitHub secrets for Lambda environment variables
- Uses Docker to bundle Python dependencies (PyJWT, requests)

---

## 🔐 Required GitHub Secrets

Configure these in: **Settings → Secrets and variables → Actions → Repository secrets**

### Common Secrets (All Workflows)

| Secret Name             | Description        | Example                                    |
| ----------------------- | ------------------ | ------------------------------------------ |
| `AWS_ACCESS_KEY_ID`     | AWS IAM access key | `AKIAIOSFODNN7EXAMPLE`                     |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_DEFAULT_REGION`    | Default AWS region | `us-east-1`                                |

### Auth Stack Specific Secrets ⭐

| Secret Name     | Description                   | How to Get                                                               |
| --------------- | ----------------------------- | ------------------------------------------------------------------------ |
| `JWT_SECRET`    | Secret for signing JWT tokens | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `IMAGE_API_URL` | Image API endpoint            | From `infra_images` stack output                                         |
| `IMAGE_API_KEY` | Image API key                 | `aws apigateway get-api-key --api-key <ID> --include-value`              |
| `TEXT_API_URL`  | Text API endpoint             | From `infra` stack output                                                |
| `TEXT_API_KEY`  | Text API key                  | `aws apigateway get-api-key --api-key <ID> --include-value`              |

### How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the name (exact match required!)
5. Paste the secret value
6. Click **Add secret**

---

## 🔄 Workflow Execution Steps

Each workflow follows a similar pattern:

### Step 1: Checkout Repository

```yaml
- uses: actions/checkout@v4
```

Downloads your repository code to the GitHub Actions runner.

### Step 2: Setup Environment

```yaml
- uses: actions/setup-node@v4 # For CDK
- uses: actions/setup-python@v4 # For Lambda/CDK
```

Installs Node.js 20 and Python 3.12.

### Step 3: Install CDK

```yaml
- run: npm install -g aws-cdk
```

Installs AWS CDK CLI globally.

### Step 4: Configure AWS Credentials

```yaml
- env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

Sets AWS credentials from GitHub secrets as environment variables.

### Step 5: Install Python Dependencies

```yaml
- run: pip install -r requirements.txt
```

Installs CDK Python libraries.

### Step 6: Show Deployment Preview

```yaml
- run: cdk diff
```

Shows what resources will be created/updated/deleted (non-blocking).

### Step 7: Bootstrap CDK (if needed)

```yaml
- run: cdk bootstrap
```

Creates S3 bucket and IAM roles for CDK deployments (idempotent).

### Step 8: Backup Current Stack

```yaml
- run: aws cloudformation describe-stacks > stack-backup.json
```

Saves current stack state for emergency rollback.

### Step 9: Deploy to Production

```yaml
- run: cdk deploy --require-approval never
```

Deploys infrastructure changes to AWS. Exits with error if deployment fails.

### Step 10: Show Outputs

```yaml
- run: aws cloudformation describe-stacks --query 'Stacks[0].Outputs'
```

Displays stack outputs (URLs, resource names, etc.).

---

## 🎯 Trigger Conditions

Workflows only run when **ALL** conditions are met:

1. **Branch**: Push to `main` only
2. **Files**: Changes in specific directories
3. **Environment**: `production` environment approved (optional)

### Example: When Does Auth Stack Deploy?

```yaml
on:
  push:
    branches: [main] # Must push to main
    paths: ["infra_auth_stack/**"] # Must change files here
```

**Triggers on:**

- ✅ Push to `main` changing `infra_auth_stack/app.py`
- ✅ Push to `main` changing `infra_auth_stack/services/auth.py`
- ✅ Push to `main` changing `infra_auth_stack/infra_auth_stack/infra_auth_stack_stack.py`

**Does NOT trigger on:**

- ❌ Push to `front_end` branch (not main)
- ❌ Push to `main` changing only `infra/` files
- ❌ Push to `main` changing only `README.md` (not in infra_auth_stack/)

---

## 🚨 Troubleshooting

### Deployment Failed - How to Rollback

If a deployment fails, GitHub Actions will automatically exit with error. To manually rollback:

```bash
# Option 1: Rollback via CloudFormation Console
1. Go to CloudFormation console
2. Select the failed stack
3. Click "Roll back" button

# Option 2: Rollback via AWS CLI
aws cloudformation cancel-update-stack --stack-name InfraAuthStack

# Option 3: Delete and redeploy previous version
aws cloudformation delete-stack --stack-name InfraAuthStack
# Then push previous commit to main branch
```

### Common Errors

#### ❌ "AWS credentials could not be found"

**Solution**: Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets.

#### ❌ "JWT_SECRET not set" (Auth Stack)

**Solution**: Add all required auth stack secrets to GitHub.

#### ❌ "No module named 'jwt'" (Auth Stack)

**Solution**: Ensure Docker is available in GitHub Actions runner (it is by default).

#### ❌ "Stack is in UPDATE_ROLLBACK_FAILED state"

**Solution**: Manually fix or delete the stack:

```bash
aws cloudformation delete-stack --stack-name <STACK_NAME>
```

#### ❌ "CDKToolkit stack not found"

**Solution**: Bootstrap step will handle this automatically, but you can manually bootstrap:

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

---

## 📊 Monitoring Deployments

### View Workflow Runs

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click on a workflow run to see logs
4. Expand steps to see detailed output

### View AWS Resources

```bash
# List all CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Get stack details
aws cloudformation describe-stacks --stack-name InfraAuthStack

# View stack events (for debugging)
aws cloudformation describe-stack-events --stack-name InfraAuthStack
```

---

## 🔒 Security Best Practices

### ✅ DO

- Store ALL secrets in GitHub Secrets (never in code)
- Use `production` environment for additional approval layer
- Review deployment previews before approving
- Keep IAM user permissions minimal (only what CDK needs)
- Rotate AWS credentials regularly

### ❌ DON'T

- Never commit `.env` files to the repository
- Never hardcode API keys or secrets in code
- Never push directly to `main` without testing
- Never disable deployment previews (`cdk diff`)
- Never skip stack backups

---

## 🎯 Quick Reference

### Deploy Specific Stack Manually

```bash
# Image stack
cd infra_images && cdk deploy

# Text stack
cd infra && cdk deploy

# Frontend stack
cd infra_frontend && cdk deploy --context env_name=prod

# Auth stack
cd infra_auth_stack && cdk deploy
```

### Test Workflow Locally (with act)

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run a specific workflow
act -W .github/workflows/deploy-auth.yml

# Run with secrets
act -W .github/workflows/deploy-auth.yml --secret-file .secrets
```

### View Workflow Syntax

```bash
# Validate workflow YAML
npx yaml-lint .github/workflows/*.yml
```

---

## 📝 Workflow Comparison

| Feature             | Image              | Text         | Frontend             | Auth                     |
| ------------------- | ------------------ | ------------ | -------------------- | ------------------------ |
| **Region**          | us-west-2          | eu-west-3    | Configurable         | eu-west-3                |
| **Trigger Path**    | `infra_images/**`  | `infra/**`   | `infra_frontend/**`  | `infra_auth_stack/**`    |
| **Bootstrap**       | ✅ Yes             | ❌ No        | ❌ No                | ✅ Yes                   |
| **Docker**          | ❌ No              | ❌ No        | ❌ No                | ✅ Yes (Lambda bundling) |
| **Extra Secrets**   | 0                  | 0            | 0                    | 5 (JWT + API keys)       |
| **Deployment Time** | ~2-3 min           | ~1-2 min     | ~3-5 min             | ~3-4 min                 |
| **Stack Name**      | `InfraImagesStack` | `InfraStack` | `prod-FrontendStack` | `InfraAuthStack`         |

---

## 🚀 Adding a New Workflow

To add a new deployment workflow:

1. **Create workflow file**: `.github/workflows/deploy-your-stack.yml`
2. **Copy existing workflow** as template
3. **Update**:
   - Workflow name
   - Trigger paths
   - Working directory
   - Region
   - Stack name
   - Any special requirements
4. **Test locally** with `act` (optional)
5. **Commit and push** to a feature branch
6. **Merge to main** to activate

---

## 📞 Support

- **GitHub Actions Docs**: https://docs.github.com/actions
- **AWS CDK Docs**: https://docs.aws.amazon.com/cdk
- **CloudFormation Docs**: https://docs.aws.amazon.com/cloudformation

---

**Last Updated**: November 2025  
**Maintained By**: Repository maintainers
