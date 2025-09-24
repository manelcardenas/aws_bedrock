import base64
import boto3
import json
import logging
import os
from botocore.exceptions import ClientError
from time import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AWS_REGION_BEDROCK = "us-west-2"
S3_BUCKET = os.getenv("S3_BUCKET")
if not S3_BUCKET:
    raise ValueError("S3_BUCKET is not set")

client = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION_BEDROCK)
s3_client = boto3.client(service_name="s3")


def get_titan_config(description: str):
    return json.dumps(
        {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": description},
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 512,
                "width": 512,
                "cfgScale": 8.0,
            },
        }
    )


def save_image_to_s3(base64_image: str):
    image_file = base64.b64decode(base64_image)
    timestamp = int(time())
    image_name = str(timestamp) + ".jpg"

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=image_name,
        Body=image_file,
    )

    signed_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": image_name},
        ExpiresIn=1000,
    )
    return signed_url


def handler(event, context):
    try:
        body = json.loads(event["body"])
        description = body.get("description")
        if not description:
            logger.error("Missing description in the request body")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing description"}),
            }
        titan_config = get_titan_config(description)
        response = client.invoke_model(
            body=titan_config,
            modelId="amazon.titan-image-generator-v1",
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        if not response_body.get("images"):
            raise ValueError("No images returned by model")
        base64_image = response_body.get("images")[0]
        signed_url = save_image_to_s3(base64_image)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"image_url": signed_url}),
        }
    except ClientError as e:
        logger.error(f"AWS service error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "AWS service error"}),
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Unexpected internal error"}),
        }
