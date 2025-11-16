#!/usr/bin/env python3

import aws_cdk as cdk

from infra_auth_stack.infra_auth_stack_stack import InfraAuthStackStack


app = cdk.App()

# Configuration
ENV_NAME = "prod"  # Environment name for resource naming
AWS_REGION = "eu-west-3"  # Your preferred region

InfraAuthStackStack(
    app,
    "InfraAuthStack",
    env_name=ENV_NAME,
    env=cdk.Environment(
        region=AWS_REGION,
    ),
)

app.synth()
