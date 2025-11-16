#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra_frontend.frontend_stack import FrontendStack

app = cdk.App()
env_name = app.node.try_get_context("env_name") or "dev"

FrontendStack(
    app,
    f"{env_name}-FrontendStack",
    env_name=env_name,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
