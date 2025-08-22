import boto3
import os
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()


def main():
    client = boto3.client(service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION"))

    model_id = os.getenv("MODEL_ID")

    prompt = "Explain the concept of quantum computing in a way that is easy to understand."


    request = json.dumps({
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature": 0,
    })

    try:
        # Invoke the model with the request.
        streaming_response = client.invoke_model_with_response_stream(
            modelId=model_id, body=request
        )

        # Extract and print the response text in real-time.
        for event in streaming_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if "generation" in chunk:
                print(chunk["generation"], end="")

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)


if __name__ == "__main__":
    main()
