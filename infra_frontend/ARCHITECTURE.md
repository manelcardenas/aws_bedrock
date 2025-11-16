# Frontend Architecture

## Overview

The Bedrock Playground frontend is deployed using a **serverless static hosting architecture** on AWS, combining S3 for storage and CloudFront for global content delivery.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  User's Browser (Anywhere in the World)                              │
│    ↓                                                                  │
│    │ HTTPS Request (login.html, index.html, CSS, JS)                 │
│    ↓                                                                  │
│  ┌──────────────────────────────────────────────────────┐            │
│  │  Amazon CloudFront (Global CDN)                      │            │
│  │  • 450+ Edge Locations worldwide                     │            │
│  │  • SSL/TLS Termination                               │            │
│  │  • Caching (24h TTL for static assets)               │            │
│  │  • Gzip/Brotli compression                           │            │
│  │  • Security headers (HSTS, XSS protection, etc.)     │            │
│  └─────────────────────┬────────────────────────────────┘            │
│                        ↓                                              │
│                        │ Origin Request (cache miss)                 │
│                        ↓                                              │
│  ┌──────────────────────────────────────────────────────┐            │
│  │  Amazon S3 (Private Bucket)                          │            │
│  │  • prod-bedrock-playground-969341425463              │            │
│  │  • Static files: HTML, CSS, JS                       │            │
│  │  • Versioning enabled (prod only)                    │            │
│  │  • Not publicly accessible                           │            │
│  │  • Access via CloudFront OAI only                    │            │
│  └──────────────────────────────────────────────────────┘            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

Frontend JavaScript makes authenticated API calls:
    ↓
┌─────────────────────────────────────────────────┐
│  Auth Proxy Lambda (eu-west-3)                  │
│  • Validates JWT token                          │
│  • Forwards to backend APIs                     │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  Backend APIs                                   │
│  • Image Generation (us-west-2)                 │
│  • Text Summarization (eu-west-3)               │
└─────────────────────────────────────────────────┘
```

## Architecture Components

### 1. Amazon S3 (Simple Storage Service)

**What it is:**

- Object storage service for static files
- Highly durable (99.999999999% durability)
- Highly available (99.99% availability)

**Why we use it:**

- **Cost-effective**: Pay only for storage used (~$0.023/GB/month)
- **Reliable**: Redundant storage across multiple facilities
- **Scalable**: No capacity planning needed
- **Static website hosting**: Native support for HTML, CSS, JS files

**Configuration:**

```python
aws_s3.Bucket(
    block_public_access=BLOCK_ALL,      # Security: not publicly accessible
    versioned=True,                      # Track file changes (prod only)
    removal_policy=DESTROY/RETAIN,       # Auto-delete in dev, keep in prod
    cors=[...]                           # Allow API calls from frontend
)
```

**Cost (estimated for this project):**

- Storage: ~10 MB of files = $0.0002/month
- PUT requests (deployments): ~100 requests/month = $0.0005
- GET requests: Minimal (served by CloudFront)
- **Total S3: < $0.01/month**

### 2. Amazon CloudFront (Content Delivery Network)

**What it is:**

- Global CDN with 450+ edge locations across 90+ cities
- Caches content close to users for fast delivery
- Provides SSL/TLS encryption for secure connections

**Why we use it:**

- **Performance**: Sub-100ms response times globally (vs 200-500ms from single region)
- **Security**:
  - Free SSL/TLS certificates via AWS Certificate Manager
  - DDoS protection via AWS Shield Standard
  - Origin Access Identity (OAI) - S3 bucket stays private
  - Security headers (HSTS, XSS protection, frame options)
- **Cost optimization**: Reduces S3 data transfer costs
- **Reliability**: 99.9% SLA, automatic failover

**Configuration:**

```python
aws_cloudfront.Distribution(
    default_behavior={
        cache_policy: 24h TTL,           # Cache static files for 1 day
        viewer_protocol: REDIRECT_TO_HTTPS,  # Force HTTPS
        compress: True,                   # Gzip/Brotli compression
        allowed_methods: GET/HEAD/OPTIONS
    },
    price_class: PRICE_CLASS_ALL,        # All edge locations (prod)
    enable_ipv6: True,                   # IPv6 support
    error_responses: [                   # SPA routing support
        403 → 200 /index.html,
        404 → 200 /index.html
    ]
)
```

**Cost (estimated for this project):**

- Data transfer out (first 10 TB/month): ~1 GB = $0.085
- HTTPS requests (first 10M/month): ~10,000 requests = $0.01
- SSL certificate: FREE via AWS Certificate Manager
- **Total CloudFront: ~$0.10/month**

### 3. Origin Access Identity (OAI)

**What it is:**

- Special CloudFront user identity
- Allows CloudFront to access private S3 buckets
- S3 bucket policy grants read access only to this OAI

**Why we use it:**

- **Security**: S3 bucket never exposed to public internet
- **Access control**: Only CloudFront can access files
- **Best practice**: Defense-in-depth security

### 4. Security Headers

**Implemented headers:**

```
Strict-Transport-Security: max-age=31536000; includeSubdomains
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

**Protection against:**

- Man-in-the-middle attacks (HTTPS enforcement)
- Clickjacking attacks (frame options)
- MIME type sniffing vulnerabilities
- Cross-site scripting (XSS) attacks

## Alternative Architectures (Not Used)

### 1. AWS Amplify Hosting

**What it is:** Fully managed hosting for static sites and SPAs

**Pros:**

- Integrated CI/CD from Git repositories
- Built-in preview environments
- Automatic SSL certificate management

**Cons:**

- **Cost**: ~$0.15/GB data transfer (vs $0.085 for CloudFront)
- Less control over caching policies
- Vendor lock-in to Amplify ecosystem
- Overkill for simple static site

**Why we didn't use it:** More expensive, less flexible, unnecessary features for our use case

### 2. Netlify / Vercel (External Services)

**What it is:** Third-party hosting platforms with global CDN

**Pros:**

- Extremely easy deployment (git push to deploy)
- Built-in form handling, serverless functions
- Great developer experience

**Cons:**

- **Cost**: $0/month free tier limited, then $19+/month
- Data egress to AWS services: Additional latency + costs
- Less control over infrastructure
- Not within AWS VPC/network (higher latency to backend APIs)

**Why we didn't use it:** Increases latency between frontend and backend, additional cost, less AWS integration

### 3. EC2 with Nginx (Traditional Server)

**What it is:** Virtual machine running web server

**Pros:**

- Full control over server configuration
- Can serve dynamic content
- Familiar for traditional ops teams

**Cons:**

- **Cost**: ~$10-30/month minimum (vs $0.10 for CloudFront+S3)
- Requires patching, maintenance, monitoring
- Single point of failure (need load balancer + auto-scaling for HA)
- Manual SSL certificate management
- No global CDN (slow for international users)

**Why we didn't use it:** Massive overkill for static files, expensive, requires maintenance

### 4. S3 Static Website Hosting (No CloudFront)

**What it is:** S3's built-in static website hosting feature

**Pros:**

- Simplest possible setup
- Very low cost

**Cons:**

- **No HTTPS support** (HTTP only)
- No custom SSL certificates
- Slower (no CDN, single region)
- No security headers
- No caching optimization
- Bucket must be publicly accessible (security risk)

**Why we didn't use it:** No HTTPS, poor security, slow performance for global users

## Cost Breakdown

### Monthly Costs (Estimated)

| Service        | Component                 | Cost                           |
| -------------- | ------------------------- | ------------------------------ |
| **S3**         | Storage (10 MB)           | $0.0002                        |
| **S3**         | PUT requests (100)        | $0.0005                        |
| **S3**         | GET requests              | $0.00 (cached by CloudFront)   |
| **CloudFront** | Data transfer (1 GB)      | $0.085                         |
| **CloudFront** | HTTPS requests (10K)      | $0.01                          |
| **CloudFront** | SSL certificate           | $0.00 (free)                   |
| **Route 53**   | Hosted zone (optional)    | $0.50 (if using custom domain) |
| **Total**      | **Without custom domain** | **~$0.10/month**               |
| **Total**      | **With custom domain**    | **~$0.60/month**               |

### Cost at Scale

**10,000 users/month (100 MB data transfer):**

- CloudFront: ~$8.50/month
- S3: ~$0.10/month
- **Total: ~$8.60/month**

**100,000 users/month (1 GB data transfer):**

- CloudFront: ~$85/month
- S3: ~$0.50/month
- **Total: ~$85.50/month**

**Comparison with alternatives:**

- EC2 t3.small (same scale): ~$15-30/month + no global CDN
- Amplify: ~$150/month (1 GB data transfer)
- Netlify Pro: $19/month + overages
- Vercel Pro: $20/month + overages

## Performance Characteristics

### Latency (Time to First Byte)

| Location   | CloudFront (with cache) | CloudFront (cache miss) | S3 Direct | EC2 us-west-2 |
| ---------- | ----------------------- | ----------------------- | --------- | ------------- |
| California | **15-30ms**             | 80-100ms                | 80-100ms  | 10-20ms       |
| New York   | **20-40ms**             | 150-180ms               | 150-180ms | 80-100ms      |
| London     | **25-50ms**             | 180-220ms               | 180-220ms | 150-180ms     |
| Tokyo      | **30-60ms**             | 200-250ms               | 200-250ms | 120-150ms     |
| Sydney     | **40-80ms**             | 220-280ms               | 220-280ms | 150-200ms     |

### Cache Hit Ratio

- **Expected**: 85-95% for static assets
- **Impact**: 85-95% of requests served from edge locations (fast)
- **Result**: Very low load on S3 origin

## Deployment Process

### What Happens During `cdk deploy`:

1. **Synthesis** (5-10s):

   - CDK generates CloudFormation template
   - Bundles frontend assets

2. **Asset Publishing** (20-60s):

   - Frontend files uploaded to CDK staging bucket
   - Lambda functions (if any) packaged and uploaded

3. **CloudFormation Deployment** (3-5 minutes first time, 1-2 minutes updates):

   - S3 bucket created/updated
   - CloudFront distribution created/updated (slowest step)
   - Origin Access Identity created
   - Bucket policies applied

4. **BucketDeployment** (30-60s):

   - Files copied from CDK staging to website bucket
   - Old files pruned (if enabled)
   - CloudFront cache invalidated

5. **CloudFront Propagation** (5-10 minutes):
   - Distribution changes propagate to all edge locations
   - During this time, some edge locations may serve old content

**Total time: 4-8 minutes for first deployment, 2-4 minutes for updates**

## Best Practices Implemented

### Security

✅ S3 bucket not publicly accessible  
✅ CloudFront enforces HTTPS only  
✅ Security headers on all responses  
✅ Origin Access Identity for S3 access  
✅ CORS configured for API calls only

### Performance

✅ Compression enabled (Gzip + Brotli)  
✅ Long cache TTL for static assets (24h)  
✅ IPv6 enabled  
✅ All edge locations used (prod)

### Reliability

✅ S3 versioning enabled (prod)  
✅ CloudFront automatic failover  
✅ Error page routing for SPA

### Cost Optimization

✅ CDN reduces origin requests  
✅ Compression reduces data transfer  
✅ Long cache TTL reduces CloudFront costs  
✅ Dev environment uses fewer edge locations

### Operations

✅ Infrastructure as Code (CDK)  
✅ Automatic cache invalidation on deploy  
✅ Stack outputs for easy reference  
✅ Environment-based configuration (dev/prod)

## Monitoring & Debugging

### CloudFront Metrics (Available in Console)

- **Requests**: Total number of requests
- **Bytes Downloaded**: Data transfer volume
- **4xx/5xx Error Rates**: Client/server errors
- **Cache Hit Rate**: Percentage served from cache

### S3 Metrics

- **Bucket Size**: Total storage used
- **Number of Objects**: File count
- **Requests**: GET/PUT operations

### How to Check Deployment Status

```bash
# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name prod-FrontendStack

# Check CloudFront distribution status
aws cloudfront get-distribution --id E1YM6SXPVKR3LD

# List files in S3 bucket
aws s3 ls s3://prod-bedrock-playground-969341425463/

# Invalidate CloudFront cache manually
aws cloudfront create-invalidation --distribution-id E1YM6SXPVKR3LD --paths '/*'
```

## Summary

Our frontend architecture uses **CloudFront + S3** for:

- ✅ **Low cost**: ~$0.10/month for typical usage
- ✅ **High performance**: <50ms latency globally
- ✅ **High availability**: 99.9% SLA
- ✅ **Security**: HTTPS, security headers, private origin
- ✅ **Scalability**: Handle millions of requests automatically
- ✅ **Low maintenance**: Fully managed services, no servers to patch

This is the **industry standard** for hosting modern single-page applications and static websites.
