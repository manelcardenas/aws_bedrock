from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_lambda,
    aws_apigateway,
    aws_iam,
    aws_s3,
    Tags,
)
from constructs import Construct


class InfraImagesStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, env_name: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 🏷️ ADD TAGS for resource organization (env_name is just a placeholder for the environment name)
        Tags.of(self).add("Project", "ImageGeneration")
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("ManagedBy", "CDK")

        # 📂 S3 BUCKET for storing images
        image_bucket = aws_s3.Bucket(
            self,
            id="ImageBucket",
            # Environment variable for the S3 bucket
            bucket_name=f"{env_name}-image-generation-bucket-{self.account}",
            # 🔒 Block public access
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            # 📦 Lifecycle rule to expire objects after 30 days
            lifecycle_rules=[
                aws_s3.LifecycleRule(
                    id="DeleteAfter30Days",
                    enabled=True,
                    expiration=Duration.days(30),
                )
            ],
        )

        # 📦 LAMBDA FUNCTION for generating images
        image_lambda = aws_lambda.Function(
            self,
            id="ImageLambda",
            function_name=f"{env_name}-image-generation-lambda-{self.account}",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("services"),
            handler="image.handler",
            timeout=Duration.seconds(30),
            memory_size=512,  # more memory -> faster execution
            retry_attempts=0,  # no retries -> faster execution
            environment={
                "S3_BUCKET": image_bucket.bucket_name,
                "LOG_LEVEL": "INFO",
            },
        )

        # 🔑 GRANT READ AND WRITE ACCESS TO S3 BUCKET
        image_bucket.grant_read_write(image_lambda)
        # 🔑 GRANT ACCESS TO BEDROCK
        image_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                resources=["*"],
                actions=["bedrock:InvokeModel"],
            )
        )

        # 🌐 API GATEWAY with proper configuration
        api = aws_apigateway.RestApi(
            self,
            id="ImageApi",
            rest_api_name=f"{env_name}-image-generation-api-{self.account}",
            description="API for generating images using Bedrock",
        )

        # 🔑 API KEY - This is what clients will use to authenticate
        api_key = aws_apigateway.ApiKey(
            self,
            id="ImageApiKey",
            api_key_name="cdk-image-api-key",
            description="API Key for CDK Image Generation API",
        )

        # 📊 USAGE PLAN - Controls rate limiting and quotas
        usage_plan = aws_apigateway.UsagePlan(
            self,
            id="ImageUsagePlan",
            name="image-usage-plan",
            description="Usage plan for Image Generation API",
            # THROTTLE CONFIGURATION
            throttle=aws_apigateway.ThrottleSettings(
                rate_limit=5,  # 5 requests per second
                burst_limit=10,  # Allow bursts up to 10 requests
            ),
            # QUOTA CONFIGURATION (optional but recommended)
            quota=aws_apigateway.QuotaSettings(
                limit=1000,  # 1000 requests
                period=aws_apigateway.Period.MONTH,  # per month
            ),
        )

        # 🔗 LINK API KEY TO USAGE PLAN
        # This is CRITICAL - the API key must be associated with the usage plan
        usage_plan.add_api_key(api_key)

        # 🎯 ADD API STAGE TO USAGE PLAN
        # This connects your API's 'prod' stage to the usage plan
        usage_plan.add_api_stage(stage=api.deployment_stage, api=api)

        # 📍 CREATE ENDPOINT with API KEY REQUIRED
        image_resource = api.root.add_resource("image")
        image_integration = aws_apigateway.LambdaIntegration(image_lambda)

        # 📋 REQUEST VALIDATION MODEL
        request_model = api.add_model(
            "ImageRequestModel",
            content_type="application/json",
            model_name="ImageRequest",
            schema=aws_apigateway.JsonSchema(
                schema=aws_apigateway.JsonSchemaVersion.DRAFT4,
                type=aws_apigateway.JsonSchemaType.OBJECT,
                properties={
                    "description": aws_apigateway.JsonSchema(
                        type=aws_apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=500,
                    )
                },
                required=["description"],
            ),
        )

        # 🔍 REQUEST VALIDATOR
        request_validator = aws_apigateway.RequestValidator(
            self, "RequestValidator", rest_api=api, validate_request_body=True
        )

        # 📍 ADD METHOD WITH VALIDATION
        image_resource.add_method(
            "POST",
            image_integration,
            api_key_required=True,  # 🔐 THIS MAKES API KEY MANDATORY
            request_models={"application/json": request_model},
            request_validator=request_validator,
        )
        image_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "x-api-key"],
        )

        # 🚀 FORCE API DEPLOYMENT (ensures changes are applied)
        deployment = aws_apigateway.Deployment(
            self,
            id="ImageApiDeployment",
            api=api,
            description="Deployment for Image API with API Key",
        )
        deployment.node.add_dependency(image_resource)

        # 📤 OUTPUTS - Display important values after deployment
        CfnOutput(
            self,
            id="ApiKeyId",
            description="API Key ID (use AWS CLI to get the actual secret value)",
            value=api_key.key_id,  # This is just the ID, not the secret value
        )

        CfnOutput(
            self,
            id="ApiEndpoint",
            description="API Gateway endpoint URL",
            value=api.url,
        )

        CfnOutput(
            self,
            id="GetApiKeyCommand",
            description="Command to get the actual API key secret value",
            value=f"aws apigateway get-api-key --api-key {api_key.key_id} --include-value --region {self.region}",
        )
