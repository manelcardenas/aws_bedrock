#!/usr/bin/env python3

import aws_cdk as cdk

from infra_images.infra_images_stack import InfraImagesStack


app = cdk.App()
InfraImagesStack(
    app,
    "InfraImagesStack",
)

app.synth()
