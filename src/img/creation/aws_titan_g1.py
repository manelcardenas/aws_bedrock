import base64
import boto3
import json
import os
from dotenv import load_dotenv


load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION")
)

prompt = "A photo of a cat"

# Define the image generation configuration.
titan_g1_image_config = json.dumps(
    {
        "taskType": "TEXT_IMAGE",  # Required for text to image generation
        "textToImageParams": {"text": prompt},
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "height": 1024,
            "width": 1024,
            "cfgScale": 8.0,  # Control the diversity of the generated image
            "seed": 0,  # Control the randomness of the generated image
        },
    }
)

# Invoke the model with the request.
response = client.invoke_model(
    body=titan_g1_image_config,
    modelId=os.getenv("IMAGE_MODEL_ID"),
    accept="application/json",
    contentType="application/json",
)


response_body = json.loads(response.get("body").read())

base64_image = response_body.get("images")[0]
base64_bytes = base64_image.encode("ascii")
image_bytes = base64.b64decode(base64_bytes)

file_name = "images/titan_g1_image.png"
with open(file_name, "wb") as file:
    file.write(image_bytes)

print(f"The generated image has been saved to {file_name}")
