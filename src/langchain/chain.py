import boto3
import os
from dotenv import load_dotenv

from langchain_aws import BedrockLLM as LLM
from langchain_core.prompts import PromptTemplate

load_dotenv()

client = boto3.client(
    service_name="bedrock-runtime", region_name=os.getenv("AWS_REGION")
)

model_id = os.getenv("MODEL_ID")

llm = LLM(model_id=model_id, client=client)


def invoke_model(prompt: str):
    return llm.invoke(prompt)


def chain():
    prompt = PromptTemplate.from_template("What is the capital of {country}?")
    chain = prompt | llm
    return chain.invoke({"country": "France"})


print(chain())
