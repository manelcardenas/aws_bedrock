from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration,
    aws_s3,
    aws_s3_deployment,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_iam,
    Tags,
)
from constructs import Construct


class FrontendStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, env_name: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 🏷️ ADD TAGS for resource organization
        Tags.of(self).add("Project", "BedrockPlayground")
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("ManagedBy", "CDK")

        # 🪣 S3 BUCKET for static website hosting
        website_bucket = aws_s3.Bucket(
            self,
            id="WebsiteBucket",
            bucket_name=f"{env_name}-bedrock-playground-{self.account}",
            # 🔒 Block all public access (CloudFront will handle access)
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            # 🗑️ Auto-delete bucket on stack deletion (for dev/test environments)
            removal_policy=RemovalPolicy.DESTROY
            if env_name != "prod"
            else RemovalPolicy.RETAIN,
            auto_delete_objects=True if env_name != "prod" else False,
            # 📦 Versioning for production
            versioned=True if env_name == "prod" else False,
            # 🌐 CORS configuration for API calls
            cors=[
                aws_s3.CorsRule(
                    allowed_methods=[
                        aws_s3.HttpMethods.GET,
                        aws_s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
        )

        # 🔐 Origin Access Identity for CloudFront
        # This allows CloudFront to access the S3 bucket privately
        origin_access_identity = aws_cloudfront.OriginAccessIdentity(
            self,
            "OAI",
            comment=f"OAI for {env_name} Bedrock Playground",
        )

        # 📜 Grant CloudFront read access to S3 bucket
        website_bucket.grant_read(origin_access_identity)

        # 🌐 CLOUDFRONT DISTRIBUTION
        # Cache policy for static assets (HTML, CSS, JS)
        cache_policy = aws_cloudfront.CachePolicy(
            self,
            "CachePolicy",
            cache_policy_name=f"{env_name}-bedrock-playground-cache",
            comment="Cache policy for Bedrock Playground static assets",
            default_ttl=Duration.hours(24),
            max_ttl=Duration.days(365),
            min_ttl=Duration.seconds(0),
            # Cache based on query strings for API compatibility
            query_string_behavior=aws_cloudfront.CacheQueryStringBehavior.all(),
            # Enable compression for better performance
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
        )

        # Response headers policy for security
        response_headers_policy = aws_cloudfront.ResponseHeadersPolicy(
            self,
            "ResponseHeadersPolicy",
            response_headers_policy_name=f"{env_name}-security-headers",
            comment="Security headers for Bedrock Playground",
            # CORS configuration
            cors_behavior=aws_cloudfront.ResponseHeadersCorsBehavior(
                access_control_allow_origins=["*"],
                access_control_allow_methods=["GET", "HEAD", "OPTIONS"],
                access_control_allow_headers=["*"],
                access_control_allow_credentials=False,
                origin_override=True,
            ),
            # Security headers
            security_headers_behavior=aws_cloudfront.ResponseSecurityHeadersBehavior(
                # Prevent clickjacking
                frame_options=aws_cloudfront.ResponseHeadersFrameOptions(
                    frame_option=aws_cloudfront.HeadersFrameOption.SAMEORIGIN,
                    override=True,
                ),
                # Prevent MIME type sniffing
                content_type_options=aws_cloudfront.ResponseHeadersContentTypeOptions(
                    override=True
                ),
                # XSS protection
                xss_protection=aws_cloudfront.ResponseHeadersXSSProtection(
                    protection=True,
                    mode_block=True,
                    override=True,
                ),
                # Referrer policy
                referrer_policy=aws_cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=aws_cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
                    override=True,
                ),
                # Strict Transport Security (HTTPS only)
                strict_transport_security=aws_cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.days(365),
                    include_subdomains=True,
                    override=True,
                ),
            ),
        )

        # CloudFront distribution
        distribution = aws_cloudfront.Distribution(
            self,
            "Distribution",
            comment=f"{env_name} Bedrock Playground CDN",
            default_root_object="index.html",
            # S3 origin
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3Origin(
                    bucket=website_bucket,
                    origin_access_identity=origin_access_identity,
                ),
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cache_policy,
                response_headers_policy=response_headers_policy,
                allowed_methods=aws_cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                compress=True,
            ),
            # Error responses - serve index.html for SPA routing
            error_responses=[
                aws_cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
                aws_cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
            ],
            # Enable IPv6
            enable_ipv6=True,
            # Price class - use all edge locations for production
            price_class=aws_cloudfront.PriceClass.PRICE_CLASS_ALL
            if env_name == "prod"
            else aws_cloudfront.PriceClass.PRICE_CLASS_100,
            # Enable logging for production
            enable_logging=True if env_name == "prod" else False,
        )

        # 📤 DEPLOY WEBSITE CONTENT to S3
        aws_s3_deployment.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[
                # Deploy from the src/frontend directory
                aws_s3_deployment.Source.asset("../src/frontend")
            ],
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"],  # Invalidate all CloudFront cache
            # Additional options
            memory_limit=256,  # MB
            prune=True,  # Remove files from bucket that are not in source
        )

        # 📤 OUTPUTS - Display important values after deployment
        CfnOutput(
            self,
            id="WebsiteBucketName",
            description="S3 bucket name for website hosting",
            value=website_bucket.bucket_name,
        )

        CfnOutput(
            self,
            id="DistributionId",
            description="CloudFront distribution ID",
            value=distribution.distribution_id,
        )

        CfnOutput(
            self,
            id="DistributionDomainName",
            description="CloudFront distribution domain name",
            value=distribution.distribution_domain_name,
        )

        CfnOutput(
            self,
            id="WebsiteURL",
            description="Website URL (use this to access your frontend)",
            value=f"https://{distribution.distribution_domain_name}",
        )

        CfnOutput(
            self,
            id="CacheInvalidationCommand",
            description="Command to invalidate CloudFront cache after updates",
            value=f"aws cloudfront create-invalidation --distribution-id {distribution.distribution_id} --paths '/*'",
        )
