import base64
import boto3
import json
import os
from dotenv import load_dotenv
import numpy as np


load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION")
)

model_id = os.getenv("EMBED_MODEL_ID")


# Helper functions for cosine similarity
def cosine_similarity(vec1, vec2):
    v1, v2 = np.array(vec1), np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


images = [
    "images/titan_g1_image.png",
    "images/titan_g1_image_edit.png",
    "images/stability_image_2.png",
]


def get_embeddings(image_path: str) -> list[float]:
    with open(image_path, "rb") as image:
        base_image = base64.b64encode(image.read()).decode("utf8")

    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps({"inputImage": base_image}),
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    return response_body["embedding"]


images_embeddings = []
for image in images:
    images_embeddings.append({"Path": image, "embedding": get_embeddings(image)})

test_image = "images/stability_image.png"
test_image_embedding = get_embeddings(test_image)

for image_embedding in images_embeddings:
    similarity = cosine_similarity(test_image_embedding, image_embedding["embedding"])
    print(
        f"Similarity between {test_image} and {image_embedding['Path']}: {similarity:.3f}"
    )
