import boto3
import os
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

history = []

def get_history():
        return "\n".join(history)

def get_config():
     return json.dumps({
        "inputText": get_history(),
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0,
        }
     })

def main():
    client = boto3.client(service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION"))

    model_id = os.getenv("MODEL_ID")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                break
            if not user_input.strip():
                continue
            history.append("User: " + user_input)
            response = client.invoke_model(
                modelId=model_id,
                body=get_config(),
                accept="application/json",
                contentType="application/json",
            )
            model_response = json.loads(response["body"].read())
            results = model_response.get("results", [])
            output_text = results[0].get("outputText", "").strip()
            print(output_text)
            history.append(output_text)
                    
        except (ClientError, Exception) as e:
            print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
            exit(1)



if __name__ == "__main__":
    main()
