import aws_cdk as core
import aws_cdk.assertions as assertions

from infra_frontend.frontend_stack import FrontendStack


def test_s3_bucket_created():
    app = core.App()
    stack = FrontendStack(app, "test-stack", env_name="test")
    template = assertions.Template.from_stack(stack)

    # Verify S3 bucket is created
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_cloudfront_distribution_created():
    app = core.App()
    stack = FrontendStack(app, "test-stack", env_name="test")
    template = assertions.Template.from_stack(stack)

    # Verify CloudFront distribution is created
    template.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_origin_access_identity_created():
    app = core.App()
    stack = FrontendStack(app, "test-stack", env_name="test")
    template = assertions.Template.from_stack(stack)

    # Verify CloudFront OAI is created
    template.resource_count_is("AWS::CloudFront::CloudFrontOriginAccessIdentity", 1)
