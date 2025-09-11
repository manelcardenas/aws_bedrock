import boto3
import json

client = boto3.client(service_name="bedrock-runtime", region_name="eu-west-3")


def get_config(text: str, points: int) -> str:
    prompt = f"Summarize the following text into {points} points: {text}"
    return json.dumps(
        {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 4096,
                "stopSequences": [],
                "temperature": 0,
                "topP": 1,
            },
        }
    )


# Lambda handler
# API Gateway event
def handler(event, context):
    body = json.loads(event["body"])
    text = body.get("text")
    points = event["queryStringParameters"]["points"]
    if text and points:
        config = get_config(text, points)
        response = client.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=config,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        result = response_body.get("results")[0].get("outputText")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"summary": result}),
        }

    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing text or points"}),
        }
