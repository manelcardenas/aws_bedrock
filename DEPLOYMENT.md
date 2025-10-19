# 🚀 Quick Deployment Guide

Step-by-step guide to deploy the complete AWS Bedrock Playground.

## 📋 Prerequisites Checklist

- [ ] AWS CLI installed and configured
- [ ] AWS account with Bedrock access enabled
- [ ] Python 3.12+ installed
- [ ] Node.js 20+ installed
- [ ] AWS CDK CLI installed: `npm install -g aws-cdk`

## 🎯 Deployment Steps

### Step 1: Deploy Text Summary Backend

```bash
# Navigate to text summary infrastructure
cd infra

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy
cdk deploy

# Save the outputs
# - ApiEndpoint: https://xxxxx.execute-api.eu-west-3.amazonaws.com/prod/
# - ApiKeyId: xxxxxxxxx
```

**Get the API Key:**
```bash
aws apigateway get-api-key --api-key YOUR_KEY_ID --include-value --region eu-west-3
```

Save the `value` field - you'll need it later!

---

### Step 2: Deploy Image Generation Backend

```bash
# Navigate to image generation infrastructure
cd ../infra_images

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deploy
cdk deploy

# Save the outputs
# - ApiEndpoint: https://yyyyy.execute-api.us-west-2.amazonaws.com/prod/
# - ApiKeyId: yyyyyyyyy
```

**Get the API Key:**
```bash
aws apigateway get-api-key --api-key YOUR_KEY_ID --include-value --region us-west-2
```

---

### Step 3: Deploy Frontend

```bash
# Navigate to frontend infrastructure
cd ../infra_frontend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deploy to production
cdk deploy --context env_name=prod

# Save the outputs
# - WebsiteURL: https://xxxxx.cloudfront.net
# - DistributionId: EXXXXXXXXX
```

---

### Step 4: Configure Frontend

1. **Open the CloudFront URL** from Step 3 output in your browser
2. **Scroll to Configuration section**
3. **Enter your settings:**
   - Text API URL: From Step 1 (append `/text` to the endpoint)
   - Image API URL: From Step 2 (append `/image` to the endpoint)
   - API Key: Use the same key for both (or create separate keys)
4. **Click "Save Configuration"**

---

### Step 5: Test Everything! 🎉

#### Test Text Summarization
1. Enter some text (e.g., a paragraph from an article)
2. Select number of points (3-5)
3. Click "Summarize"
4. Verify the summary appears

#### Test Image Generation
1. Enter a description (e.g., "A sunset over mountains")
2. Click "Generate Image"
3. Wait 10-15 seconds
4. Verify the image appears

---

## 🔄 Setup CI/CD (Optional)

### Configure GitHub Secrets

In your GitHub repository, go to **Settings → Secrets → Actions** and add:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1  # Optional
```

### Test Automatic Deployment

```bash
# Make a change to frontend
echo "<!-- Updated -->" >> src/frontend/index.html

# Commit and push
git add .
git commit -m "Test automatic deployment"
git push origin main

# Monitor deployment
# Go to GitHub → Actions tab
```

---

## 📊 Verify Deployment

### Check Backend APIs

**Text Summary API:**
```bash
curl -X POST "https://YOUR_TEXT_API/prod/text?points=3" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"text":"AWS Bedrock is a fully managed service that offers a choice of high-performing foundation models."}'
```

**Image Generation API:**
```bash
curl -X POST "https://YOUR_IMAGE_API/prod/image" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"description":"A beautiful sunset"}'
```

### Check Frontend

```bash
# Test CloudFront is serving files
curl -I https://YOUR_CLOUDFRONT_URL
# Should return: HTTP/2 200
```

---

## 🎛️ Configuration Summary

After deployment, you should have:

| Component | Region | URL | Notes |
|-----------|--------|-----|-------|
| Text API | eu-west-3 | https://xxxxx.execute-api.eu-west-3.amazonaws.com/prod/text | Requires ?points=N query param |
| Image API | us-west-2 | https://yyyyy.execute-api.us-west-2.amazonaws.com/prod/image | Stores images in S3 |
| Frontend | Global | https://xxxxx.cloudfront.net | CloudFront CDN |
| Image Storage | us-west-2 | S3 bucket | 30-day lifecycle |

---

## 🧹 Cleanup (Optional)

To delete all resources and avoid charges:

```bash
# Delete frontend
cd infra_frontend
cdk destroy --context env_name=prod

# Delete image API
cd ../infra_images
cdk destroy

# Delete text API
cd ../infra
cdk destroy
```

⚠️ **Warning:** This will permanently delete all resources including stored images!

---

## 💰 Cost Estimate

### Monthly Costs (Light Usage - ~100 requests/month)

| Service | Usage | Est. Cost |
|---------|-------|-----------|
| Lambda | 100 invocations, 512MB, 10s avg | ~$0.00 |
| API Gateway | 100 requests | ~$0.00 |
| Bedrock Text | 100 requests, ~500 tokens avg | ~$0.15 |
| Bedrock Images | 10 images | ~$0.80 |
| S3 | 1GB storage, 100 requests | ~$0.03 |
| CloudFront | 1GB transfer, 100 requests | ~$0.12 |
| **Total** | | **~$1.10/month** |

### Free Tier Benefits

- Lambda: 1M free requests/month
- API Gateway: 1M free requests/month (first 12 months)
- S3: 5GB free storage (first 12 months)
- CloudFront: 1TB free transfer (first 12 months)

**Most costs will be from Bedrock API calls!**

---

## 🐛 Common Issues

### Issue: `cdk bootstrap` fails
**Solution:** Ensure AWS credentials are properly configured
```bash
aws sts get-caller-identity
```

### Issue: API returns 403 Forbidden
**Solution:** Check API key is correct and usage plan is associated

### Issue: Frontend shows CORS errors
**Solution:** CORS should be configured automatically. Check API Gateway settings.

### Issue: Images not generating
**Solution:** Verify Bedrock access is enabled in us-west-2 region

### Issue: CloudFront not updating
**Solution:** Invalidate cache
```bash
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

---

## 📞 Support

If you encounter issues:

1. Check CloudWatch Logs for Lambda errors
2. Review API Gateway execution logs
3. Check CDK deployment outputs
4. Verify IAM permissions
5. Ensure Bedrock model access is enabled in your account

---

## ✅ Success Checklist

After completing all steps, you should have:

- [ ] Text Summary API deployed and working
- [ ] Image Generation API deployed and working
- [ ] Frontend accessible via CloudFront URL
- [ ] Configuration saved in browser
- [ ] Able to summarize text successfully
- [ ] Able to generate images successfully
- [ ] (Optional) GitHub Actions configured for CI/CD

---

**🎉 Congratulations! Your AWS Bedrock Playground is now live!**

Visit your CloudFront URL and start experimenting with AI! 🚀

