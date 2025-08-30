import boto3
from dotenv import load_dotenv
import os
import pprint

load_dotenv()


bedrock = boto3.client(service_name="bedrock", region_name=os.getenv("AWS_REGION"))
pprint.pprint(bedrock.list_foundation_models())
