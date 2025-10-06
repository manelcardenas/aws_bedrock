from aws_cdk import (
    aws_apigateway,
    aws_iam,
    aws_lambda,
    CfnOutput,
    Duration,
    Stack,
    Tags,
)
from constructs import Construct


class InfraStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, env_name: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 🏷️ ADD TAGS for resource organization
        Tags.of(self).add("Project", "TextSummary")
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("ManagedBy", "CDK")

        summary_lambda = aws_lambda.Function(
            self,
            id="SummaryLambda",
            function_name=f"{env_name}-text-summary-lambda-{self.account}",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("services"),
            handler="summary.handler",
            timeout=Duration.seconds(30),
            memory_size=512,
            retry_attempts=0,
            environment={
                "LOG_LEVEL": "INFO",
            },
        )

        summary_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                resources=["*"],
                actions=["bedrock:InvokeModel"],
            )
        )

        api = aws_apigateway.RestApi(
            self,
            id="SummaryApi",
            rest_api_name=f"{env_name}-text-summary-api-{self.account}",
            description="API for summarizing text",
        )

        api_key = aws_apigateway.ApiKey(
            self,
            id="SummaryApiKey",
            api_key_name="cdk-text-summary-api-key",
            description="API Key for CDK Text Summary API",
        )

        usage_plan = aws_apigateway.UsagePlan(
            self,
            id="SummaryUsagePlan",
            name="text-summary-usage-plan",
            description="Usage plan for Text Summary API",
            throttle=aws_apigateway.ThrottleSettings(
                rate_limit=5,
                burst_limit=10,
            ),
            quota=aws_apigateway.QuotaSettings(
                limit=1000,
                period=aws_apigateway.Period.MONTH,
            ),
        )

        usage_plan.add_api_key(api_key)

        usage_plan.add_api_stage(stage=api.deployment_stage, api=api)

        text_resource = api.root.add_resource("text")
        summary_integration = aws_apigateway.LambdaIntegration(summary_lambda)

        request_model = api.add_model(
            id="SummaryRequestModel",
            content_type="application/json",
            model_name="SummaryRequest",
            schema=aws_apigateway.JsonSchema(
                schema=aws_apigateway.JsonSchemaVersion.DRAFT4,
                type=aws_apigateway.JsonSchemaType.OBJECT,
                properties={
                    "text": aws_apigateway.JsonSchema(
                        type=aws_apigateway.JsonSchemaType.STRING,
                        min_length=1,
                        max_length=5000,  # Allow longer text for summarization
                    ),
                },
                required=["text"],
            ),
        )

        request_validator = aws_apigateway.RequestValidator(
            self, 
            "RequestValidator", 
            rest_api=api, 
            validate_request_body=True,
            validate_request_parameters=True  # Also validate query parameters
        )

        text_resource.add_method(
            "POST",
            summary_integration,
            api_key_required=True,
            request_models={"application/json": request_model},
            request_validator=request_validator,
            request_parameters={
                "method.request.querystring.points": True  # Required query parameter
            }
        )
        text_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "x-api-key"],
        )
        deployment = aws_apigateway.Deployment(
            self,
            id="SummaryApiDeployment",
            api=api,
            description="Deployment for Text Summary API with API Key",
        )
        deployment.node.add_dependency(text_resource)
        CfnOutput(
            self,
            id="ApiKeyId",
            description="API Key ID (use AWS CLI to get the actual secret value)",
            value=api_key.key_id,
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
