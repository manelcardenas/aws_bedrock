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


facts = [
    "A cat is a small domesticated carnivore of the family Felidae.",
    "A dog is a domesticated carnivore of the family Canidae.",
    "A bird is a warm-blooded egg-laying vertebrate animal of the class Aves.",
    "A fish is a cold-blooded aquatic vertebrate animal of the class Actinopterygii.",
    "A reptile is a cold-blooded, egg-laying, vertebrate animal of the class Reptilia.",
    "A mammal is a warm-blooded, egg-laying, vertebrate animal of the class Mammalia.",
    "A plant is a living organism of the kingdom Plantae.",
    "A mineral is a naturally occurring inorganic solid.",
    "An element is a chemical substance that cannot be broken down into simpler substances by chemical means.",
]

query = "A small domesticated carnivore"


def get_embeddings(text: str) -> list[float]:
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps({"inputText": text}),
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    return response_body["embedding"]


# Get the embeddings for the facts
fact_embeddings = []
for fact in facts:
    fact_embeddings.append(
        {
            "fact": fact,
            "embedding": get_embeddings(fact),
        }
    )


# Get the similarity between the query and the facts
query_embedding = get_embeddings(query)
for fact_embedding in fact_embeddings:
    similarity = cosine_similarity(query_embedding, fact_embedding["embedding"])
    print(
        f"Similarity between '{query}' and '{fact_embedding['fact']}': {similarity:.3f}"
    )
