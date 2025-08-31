import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION")
)
model_id = os.getenv("EMBED_MODEL_ID")

input_text = "Please recommend books with a theme similar to the movie 'Inception'."

# Create the request for the model.
request = json.dumps({"inputText": input_text})

# Invoke the model with the request.
response = client.invoke_model(modelId=model_id, body=request)

# Decode the model's native response body.
model_response = json.loads(response["body"].read())

# Extract and print the generated embedding and the input text token count.
embedding = model_response["embedding"]
input_token_count = model_response["inputTextTokenCount"]

print("\nYour input:")
print(input_text)
print(f"Number of input tokens: {input_token_count}")
print(f"Size of the generated embedding: {len(embedding)}")
print("Embedding:")
print(embedding)
