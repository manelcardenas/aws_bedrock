import boto3
import os
import json
from dotenv import load_dotenv
import base64

load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION")
)

stability_image_config = json.dumps(
    {
        "prompt": "A photo of a cat",
    }
)

# Invoke the model with the request.
response = client.invoke_model(
    modelId=os.getenv("IMAGE_MODEL_ID"),
    body=stability_image_config,
    accept="application/json",
    contentType="application/json",
)


response_body = json.loads(response.get("body").read())
base64_image_data = response_body.get("images")[0]

# Extract the image data.
image_data = base64.b64decode(base64_image_data)

# Save the generated image to a local folder.
file_name = "images/stability_image_2.png"
with open(file_name, "wb") as file:
    file.write(image_data)

print(f"The generated image has been saved to {file_name}")
