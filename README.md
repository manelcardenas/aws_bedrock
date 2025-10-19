# 🚀 AWS Bedrock Playground

A complete full-stack application for exploring AWS Bedrock AI capabilities, featuring text summarization and image generation powered by Amazon Titan models.

## 📋 Project Overview

This project demonstrates a production-ready AWS Bedrock implementation with:
- **Backend Services**: Two Lambda-based APIs (Text Summary & Image Generation)
- **Frontend Interface**: Modern web UI hosted on CloudFront + S3
- **Infrastructure as Code**: Complete AWS CDK stacks for all components
- **CI/CD Pipeline**: Automated deployments via GitHub Actions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            CloudFront CDN (Frontend)                         │
│                    HTTPS                                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│            S3 Bucket (Static Website)                        │
│         (HTML, CSS, JavaScript)                              │
└──────────────┬───────────────────┬───────────────────────────┘
               │                   │
               ▼                   ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  API Gateway     │  │  API Gateway     │
    │  (Text Summary)  │  │  (Image Gen)     │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │
             ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  Lambda Function │  │  Lambda Function │
    │  (eu-west-3)     │  │  (us-west-2)     │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │
             ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  Amazon Bedrock  │  │  Amazon Bedrock  │
    │  Titan Text      │  │  Titan Image     │
    └──────────────────┘  └──────┬───────────┘
                                 │
                                 ▼
                          ┌──────────────────┐
                          │   S3 Bucket      │
                          │  (Image Storage) │
                          └──────────────────┘
```

## 📁 Project Structure

```
bedrock/
├── src/                        # 🎮 Development Playground
│   ├── frontend/              # Frontend source code
│   │   ├── index.html
│   │   ├── css/styles.css
│   │   └── js/
│   │       ├── app.js
│   │       └── config.js
│   ├── services/              # Service implementations
│   ├── embeddings/            # Embedding examples
│   ├── img/                   # Image generation examples
│   └── langchain/             # LangChain RAG examples
│
├── infra/                      # 📝 Text Summary Backend (CDK)
│   ├── app.py
│   ├── infra/infra_stack.py
│   └── services/summary.py    # Lambda handler
│
├── infra_images/               # 🎨 Image Generation Backend (CDK)
│   ├── app.py
│   ├── infra_images/infra_images_stack.py
│   └── services/image.py      # Lambda handler
│
├── infra_frontend/             # 🌐 Frontend Infrastructure (CDK)
│   ├── app.py
│   ├── infra_frontend/frontend_stack.py
│   └── README.md
│
└── .github/workflows/          # 🔄 CI/CD Automation
    ├── deploy-text-summary.yml
    ├── deploy.yml              # Image generation deployment
    └── deploy-frontend.yml
```

## 🚀 Getting Started

### Prerequisites

- AWS CLI configured: `aws configure`
- Python 3.12+
- Node.js 20+ (for AWS CDK)
- AWS CDK CLI: `npm install -g aws-cdk`
- AWS Account with Bedrock access enabled

### Verify AWS Setup

```bash
# Check AWS configuration
aws s3 ls

# Check Bedrock access
aws bedrock list-foundation-models
```

## 🛠️ Deployment

### 1. Deploy Backend Services

#### Text Summary API
```bash
cd infra
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap  # First time only
cdk deploy
```

#### Image Generation API
```bash
cd infra_images
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk deploy
```

**Save the API endpoints and get API keys:**
```bash
# Get API key value
aws apigateway get-api-key --api-key YOUR_KEY_ID --include-value --region REGION
```

### 2. Deploy Frontend

```bash
cd infra_frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk deploy --context env_name=prod
```

**Output will provide:**
- CloudFront URL (your website URL)
- Distribution ID
- S3 bucket name

### 3. Configure Frontend

1. Open the CloudFront URL in your browser
2. Scroll to the **Configuration** section
3. Enter your API endpoints and API key
4. Click **Save Configuration**

## 🎯 Features

### Text Summarization
- Summarize text into 1-10 key points
- Uses Amazon Titan Text Express model
- Input: Up to 5000 characters
- Copy results to clipboard

### Image Generation
- Generate images from text descriptions
- Uses Amazon Titan Image Generator v1
- Output: 512x512 JPG images
- Download or open in new tab
- Images stored in S3 with 30-day lifecycle

## 🔐 Security Features

### Backend
- API Gateway with API key authentication
- Request validation and throttling
- IAM roles with least privilege
- CORS configured for frontend domain
- Rate limiting (5 req/sec, burst 10)
- Monthly quota (1000 requests)

### Frontend
- HTTPS only via CloudFront
- Private S3 bucket (no public access)
- Origin Access Identity (OAI)
- Security headers (HSTS, XSS protection, etc.)
- API keys stored in browser LocalStorage only

## 🔄 CI/CD Pipeline

The project uses GitHub Actions for automated deployments:

- **`deploy-text-summary.yml`** - Deploys text API on changes to `infra/**`
- **`deploy.yml`** - Deploys image API on changes to `infra_images/**`
- **`deploy-frontend.yml`** - Deploys frontend on changes to `infra_frontend/**` or `src/frontend/**`

### Setup GitHub Secrets

Add these secrets to your GitHub repository:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION (optional, defaults per service)
```

### Manual Deployment Trigger

```bash
git add .
git commit -m "Deploy updates"
git push origin main
```

## 💰 Cost Optimization

- CloudFront caching reduces origin requests
- S3 lifecycle rules auto-delete old images (30 days)
- Lambda functions optimized for memory/timeout
- Development environment uses fewer edge locations
- API throttling prevents unexpected costs

## 🧪 Local Development

### Test Frontend Locally
```bash
cd src/frontend
python3 -m http.server 8000
# Open http://localhost:8000
```

### Test Backend Services
```bash
cd src/services
python -m pytest
```

## 📊 Monitoring & Debugging

### View CloudWatch Logs
```bash
# Text Summary Lambda
aws logs tail /aws/lambda/ENV-text-summary-lambda-ACCOUNT --follow

# Image Generation Lambda
aws logs tail /aws/lambda/ENV-image-generation-lambda-ACCOUNT --follow
```

### Invalidate CloudFront Cache
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Check Stack Status
```bash
aws cloudformation describe-stacks --stack-name STACK_NAME
```

## 🛠️ Useful Commands

### CDK Commands
```bash
cdk ls          # List all stacks
cdk synth       # Generate CloudFormation template
cdk diff        # Compare deployed vs current state
cdk deploy      # Deploy stack
cdk destroy     # Delete stack
```

### Testing
```bash
# Backend tests
cd infra && pytest tests/

# Frontend manual testing
cd src/frontend && python3 -m http.server 8000
```

## 📝 Environment Variables

### Backend Lambda Functions
- `LOG_LEVEL` - Logging level (INFO, DEBUG, ERROR)
- `S3_BUCKET` - S3 bucket for image storage (image API only)

### CDK Deployment
- `CDK_DEFAULT_ACCOUNT` - AWS account ID
- `CDK_DEFAULT_REGION` - AWS region
- `env_name` - Environment (dev, prod) via context

## 🐛 Troubleshooting

### Issue: API calls return 403
- Verify API key is correct
- Check API Gateway deployment stage
- Ensure usage plan is associated with API key

### Issue: Images not generating
- Verify Bedrock access in us-west-2 region
- Check Lambda execution role permissions
- Review CloudWatch logs for errors

### Issue: Frontend not updating
- Clear browser cache
- Invalidate CloudFront cache
- Check S3 bucket has new files

### Issue: CDK deployment fails
- Run `cdk bootstrap` if first deployment
- Check AWS credentials are valid
- Verify account has sufficient permissions

## 📚 Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon Titan Models](https://aws.amazon.com/bedrock/titan/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)

## 🤝 Contributing

1. Make changes in respective directories
2. Test locally
3. Commit with descriptive messages
4. Push to trigger CI/CD
5. Monitor GitHub Actions for deployment status

## 📄 License

Educational project for AWS Bedrock exploration.

## 👨‍💻 Author

Built as a learning project for AWS Bedrock AI services.

---

**Happy Building! 🚀**
