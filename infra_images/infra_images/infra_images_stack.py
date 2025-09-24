from aws_cdk import (
    Duration,
    Stack,
    aws_lambda,
    aws_apigateway,
    aws_iam,
    aws_s3,
)
from constructs import Construct


class InfraImagesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image_bucket = aws_s3.Bucket(self, id="ImageBucket")

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

        image_bucket.grant_read_write(image_lambda)
        image_lambda.add_to_role_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                resources=["*"],
                actions=["bedrock:InvokeModel"],
            )
        )

        api = aws_apigateway.RestApi(self, id="ImageApi")
        image_resource = api.root.add_resource("image")
        image_integration = aws_apigateway.LambdaIntegration(image_lambda)
        image_resource.add_method("POST", image_integration)
