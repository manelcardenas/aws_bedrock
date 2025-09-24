from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_lambda,
    aws_apigateway,
    aws_iam,
    aws_s3,
    aws_cloudwatch,
)
from constructs import Construct


class InfraImagesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 📂 S3 BUCKET for storing images
        image_bucket = aws_s3.Bucket(
            self,
            id="ImageBucket",
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
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("services"),
            handler="image.handler",
            timeout=Duration.seconds(30),
            environment={
                "S3_BUCKET": image_bucket.bucket_name,
            },
        )
        # Lambda error logging to CloudWatch
        aws_cloudwatch.Alarm(
            self,
            id="ImageLambdaErrorAlarm",
            metric=image_lambda.metric_errors(),
            evaluation_periods=2,
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
            rest_api_name="Image Generation API",
            description="API for generating images using Bedrock",
        )

        # API Gateway 4xx Error Alarm
        aws_cloudwatch.Alarm(
            self,
            id="ImageApi4xxErrorAlarm",
            metric=api.metric_4xx_errors(),
            threshold=10,
            evaluation_periods=2,
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
        image_resource.add_method(
            "POST",
            image_integration,
            api_key_required=True,  # 🔐 THIS MAKES API KEY MANDATORY
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
