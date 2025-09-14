import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION_BEDROCK = "us-west-2"

client = boto3.client(
    service_name="bedrock-agent-runtime", region_name=AWS_REGION_BEDROCK
)


def handler(event, context):
    body = json.loads(event["body"])
    query = body.get("query")
    if query:
        response = client.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": os.getenv("KNOWLEDGE_BASE_ID"),
                    "modelArn": os.getenv("MODEL_ARN"),
                },
            },
        )
        answer = response.get("output").get("text")
        return {
            "statusCode": 200,
            "answer": json.dumps(answer),
        }
    return {
        "statusCode": 400,
        "error": json.dumps({"error": "query needed"}),
    }
