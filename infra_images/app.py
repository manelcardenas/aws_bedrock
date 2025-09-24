#!/usr/bin/env python3

import aws_cdk as cdk

from infra_images.infra_images_stack import InfraImagesStack


app = cdk.App()
InfraImagesStack(
    app,
    "InfraImagesStack",
    env_name="prod",  # Environment name for resource naming
)

# TODO: add boodstrap as part of the pipeline

app.synth()
