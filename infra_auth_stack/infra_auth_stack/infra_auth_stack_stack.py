import os
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_lambda,
    aws_apigateway,
    aws_dynamodb,
    aws_iam,
    Tags,
)
from constructs import Construct

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()


class InfraAuthStackStack(Stack):
    """
    Authentication and Proxy Stack

    This stack creates:
    1. DynamoDB table for user storage
    2. Auth Lambda for login (/login endpoint)
    3. Proxy Lambda for forwarding requests (/proxy/* endpoints)
    4. API Gateway with public login and protected proxy endpoints

    The proxy Lambda hides your existing API keys from the frontend!
    """

    def __init__(
        self, scope: Construct, construct_id: str, env_name: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 🏷️ ADD TAGS for resource organization
        Tags.of(self).add("Project", "AuthProxy")
        Tags.of(self).add("Environment", env_name)
        Tags.of(self).add("ManagedBy", "CDK")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🗄️ DYNAMODB TABLE for user storage
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        users_table = aws_dynamodb.Table(
            self,
            id="UsersTable",
            table_name=f"{env_name}-users-table-{self.account}",
            partition_key=aws_dynamodb.Attribute(
                name="username", type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # Auto-delete when stack destroyed
            point_in_time_recovery=True,  # Backup capability
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🔐 AUTH LAMBDA - Handles /login
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # Get configuration from environment variables
        jwt_secret = os.getenv("JWT_SECRET", "CHANGE-THIS-IN-PRODUCTION")
        jwt_expiration = os.getenv("JWT_EXPIRATION_HOURS", "24")

        auth_lambda = aws_lambda.Function(
            self,
            id="AuthLambda",
            function_name=f"{env_name}-auth-lambda-{self.account}",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset(
                "services",
                bundling={
                    "image": aws_lambda.Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="auth.login_handler",
            timeout=Duration.seconds(10),
            memory_size=256,
            retry_attempts=0,
            environment={
                "USERS_TABLE": users_table.table_name,
                "JWT_SECRET": jwt_secret,
                "JWT_EXPIRATION_HOURS": jwt_expiration,
                "LOG_LEVEL": "INFO",
            },
        )

        # Grant Lambda permission to read from DynamoDB
        users_table.grant_read_data(auth_lambda)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🔄 PROXY LAMBDA - Forwards requests to existing APIs
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # Get API URLs and keys from environment variables
        image_api_url = os.getenv("IMAGE_API_URL", "")
        image_api_key = os.getenv("IMAGE_API_KEY", "")
        text_api_url = os.getenv("TEXT_API_URL", "")
        text_api_key = os.getenv("TEXT_API_KEY", "")

        proxy_lambda = aws_lambda.Function(
            self,
            id="ProxyLambda",
            function_name=f"{env_name}-proxy-lambda-{self.account}",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset(
                "services",
                bundling={
                    "image": aws_lambda.Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="auth.proxy_handler",
            timeout=Duration.seconds(30),
            memory_size=512,
            retry_attempts=0,
            environment={
                "JWT_SECRET": jwt_secret,  # Must match auth_lambda
                "LOG_LEVEL": "INFO",
                # 🔑 YOUR EXISTING API ENDPOINTS (from .env file)
                "IMAGE_API_URL": image_api_url,
                "IMAGE_API_KEY": image_api_key,
                "TEXT_API_URL": text_api_url,
                "TEXT_API_KEY": text_api_key,
            },
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🌐 NEW API GATEWAY (authentication proxy)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        api = aws_apigateway.RestApi(
            self,
            id="AuthProxyApi",
            rest_api_name=f"{env_name}-auth-proxy-api-{self.account}",
            description="Authentication proxy for image and text APIs",
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization", "x-api-key"],
            ),
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 📍 ENDPOINT: POST /login (public, no auth required)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        login_resource = api.root.add_resource("login")
        login_integration = aws_apigateway.LambdaIntegration(auth_lambda)

        # Request validation for login
        login_model = api.add_model(
            "LoginRequestModel",
            content_type="application/json",
            model_name="LoginRequest",
            schema=aws_apigateway.JsonSchema(
                schema=aws_apigateway.JsonSchemaVersion.DRAFT4,
                type=aws_apigateway.JsonSchemaType.OBJECT,
                properties={
                    "username": aws_apigateway.JsonSchema(
                        type=aws_apigateway.JsonSchemaType.STRING,
                        min_length=1,
                    ),
                    "password": aws_apigateway.JsonSchema(
                        type=aws_apigateway.JsonSchemaType.STRING,
                        min_length=1,
                    ),
                },
                required=["username", "password"],
            ),
        )

        login_validator = aws_apigateway.RequestValidator(
            self,
            "LoginRequestValidator",
            rest_api=api,
            validate_request_body=True,
        )

        login_resource.add_method(
            "POST",
            login_integration,
            api_key_required=False,  # Login doesn't need auth!
            request_models={"application/json": login_model},
            request_validator=login_validator,
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 📍 ENDPOINT: POST /proxy/image (requires JWT in Authorization header)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        proxy_resource = api.root.add_resource("proxy")
        image_proxy_resource = proxy_resource.add_resource("image")
        image_proxy_integration = aws_apigateway.LambdaIntegration(proxy_lambda)

        image_proxy_resource.add_method(
            "POST",
            image_proxy_integration,
            api_key_required=False,  # We use JWT instead of API keys!
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 📍 ENDPOINT: POST /proxy/text (requires JWT in Authorization header)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        text_proxy_resource = proxy_resource.add_resource("text")
        text_proxy_integration = aws_apigateway.LambdaIntegration(proxy_lambda)

        text_proxy_resource.add_method(
            "POST",
            text_proxy_integration,
            api_key_required=False,  # We use JWT instead!
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🚀 FORCE API DEPLOYMENT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        deployment = aws_apigateway.Deployment(
            self,
            id="AuthProxyDeployment",
            api=api,
            description="Deployment for Auth Proxy API",
        )
        deployment.node.add_dependency(login_resource)
        deployment.node.add_dependency(image_proxy_resource)
        deployment.node.add_dependency(text_proxy_resource)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 📤 OUTPUTS - Important values after deployment
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        CfnOutput(
            self,
            id="UsersTableName",
            description="DynamoDB table for users",
            value=users_table.table_name,
        )

        CfnOutput(
            self,
            id="ApiEndpoint",
            description="Auth Proxy API Gateway endpoint URL",
            value=api.url,
        )

        CfnOutput(
            self,
            id="LoginEndpoint",
            description="Login endpoint (POST with username/password)",
            value=f"{api.url}login",
        )

        CfnOutput(
            self,
            id="ImageProxyEndpoint",
            description="Image proxy endpoint (POST with JWT token)",
            value=f"{api.url}proxy/image",
        )

        CfnOutput(
            self,
            id="TextProxyEndpoint",
            description="Text proxy endpoint (POST with JWT token)",
            value=f"{api.url}proxy/text",
        )

        CfnOutput(
            self,
            id="NextSteps",
            description="Configuration instructions",
            value="1. Add users to DynamoDB table | 2. Update proxy Lambda environment variables with real API keys | 3. Update frontend to use new auth endpoints",
        )
