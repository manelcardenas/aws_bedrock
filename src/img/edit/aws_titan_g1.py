import base64
import boto3
import json
import os
from dotenv import load_dotenv


load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION")
)

image_file_path = "images/titan_g1_image.png"
with open(image_file_path, "rb") as file:
    input_image = base64.b64encode(file.read()).decode("utf8")

# Define the image generation configuration.
titan_g1_image_edit_config = json.dumps(
    {
        "taskType": "INPAINTING",
        "inPaintingParams": {
            "text": "Add a dog on top of the cat",
            "negativeText": "bad quality, low res",
            "image": input_image,
            "maskPrompt": "On top of the cat",
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "height": 512,
            "width": 512,
            "cfgScale": 8.0,
        },
    }
)

response = client.invoke_model(
    body=titan_g1_image_edit_config,
    modelId=os.getenv("IMAGE_MODEL_ID"),
    accept="application/json",
    contentType="application/json",
)

response_body = json.loads(response.get("body").read())
base64_image = response_body.get("images")[0]
base64_bytes = base64_image.encode("ascii")
image_bytes = base64.b64decode(base64_bytes)

file_name = "images/titan_g1_image_edit.png"
with open(file_name, "wb") as file:
    file.write(image_bytes)

print(f"The generated image has been saved to {file_name}")
