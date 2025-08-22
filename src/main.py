import boto3
import pprint

def main():
    bedrock = boto3.client(service_name="bedrock", region_name="eu-west-3")
    pprint.pprint(bedrock.list_foundation_models())


if __name__ == "__main__":
    main()
