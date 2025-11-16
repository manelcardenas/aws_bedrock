# Frontend Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. Auth API URL Configuration

- [x] `src/frontend/js/config.js` has correct `AUTH_API_URL`
- [x] Current value: `https://oa2psn63h1.execute-api.eu-west-3.amazonaws.com/prod`

### 2. Frontend Files Ready

- [x] `login.html` - Login page with authentication form
- [x] `index.html` - Main app page (protected, requires JWT)
- [x] `js/config.js` - Configuration with JWT token management
- [x] `js/auth.js` - Login handler and token storage
- [x] `js/app.js` - Main app logic using Bearer token authentication
- [x] `css/styles.css` - Styles including login page

### 3. CDK Stack Ready

- [x] `frontend_stack.py` - S3 + CloudFront deployment
- [x] CloudFront will serve files from `../src/frontend`
- [x] Cache invalidation configured on deployment
- [x] HTTPS enforced with security headers

## 🚀 Deployment Options

### Option A: Manual Deployment (Local)

```bash
cd infra_frontend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Preview changes
cdk diff --context env_name=prod

# Deploy to production
cdk deploy --context env_name=prod
```

### Option B: GitHub Actions (Automated)

1. **Commit and push changes to `front_end` branch:**

   ```bash
   cd /Users/manel/Documents/zth/bedrock
   git add src/frontend/
   git add infra_frontend/
   git commit -m "feat: add JWT authentication to frontend"
   git push origin front_end
   ```

2. **Create Pull Request to main branch**

3. **Merge PR** - This will trigger `.github/workflows/deploy-frontend.yml`

4. **Monitor deployment** in GitHub Actions tab

## 📊 Expected Deployment Outputs

After successful deployment, you'll see:

```
Outputs:
WebsiteURL = https://d1234567890abc.cloudfront.net
DistributionId = E1234567890ABC
WebsiteBucketName = prod-bedrock-playground-969341425463
CacheInvalidationCommand = aws cloudfront create-invalidation --distribution-id E... --paths '/*'
```

## 🧪 Post-Deployment Testing

1. **Access the CloudFront URL** from outputs

2. **Test login page:**

   - Should see login form
   - Enter test user credentials
   - Should redirect to main app on success
   - Should show error message on failure

3. **Test authenticated app:**

   - Should see username in header
   - Should be able to generate images
   - Should be able to summarize text
   - Click logout - should return to login page

4. **Test security:**
   - Try accessing `https://your-cloudfront-url/index.html` directly (without login)
   - Should redirect to `login.html`
   - API calls should fail without valid JWT token

## 🔧 Troubleshooting

### Issue: Login returns "Failed to fetch" or network error

**Solution**: Check if auth Lambda is deployed and AUTH_API_URL is correct in config.js

### Issue: Login successful but API calls fail

**Solution**: Verify TEXT_API_URL and IMAGE_API_URL are set correctly in auth stack's proxy Lambda environment variables

### Issue: CloudFront serves old cached content

**Solution**: Run the cache invalidation command from outputs:

```bash
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths '/*'
```

### Issue: Changes not reflected after deployment

**Solution**:

1. Check if deployment completed successfully
2. Hard refresh browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
3. Clear browser cache and localStorage
4. Invalidate CloudFront cache manually

## 🔒 Security Checklist

- [x] No API keys exposed in frontend code
- [x] JWT tokens stored in localStorage (client-side only)
- [x] Token expiration check before API calls
- [x] Automatic logout on token expiration
- [x] HTTPS enforced by CloudFront
- [x] Security headers configured (HSTS, XSS protection, etc.)

## 📝 Notes

- **First-time visitors**: Will see login page
- **Login flow**: Username/password → JWT token → Access to main app
- **API calls**: Go through proxy Lambda (validates JWT, adds API keys)
- **Logout**: Clears JWT token from localStorage, redirects to login
- **Token expiration**: 24 hours (configured in auth Lambda)

## ✅ Deployment Complete!

Once deployed and tested, the frontend is ready for users to:

1. Visit the CloudFront URL
2. Login with their credentials
3. Use text summarization and image generation features
4. Logout when done

All without ever seeing or handling API keys! 🎉
