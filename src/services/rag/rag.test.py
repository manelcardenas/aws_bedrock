import json
from rag import handler

event = {
    "body": json.dumps({"query": "What does GDPR stand for?"}),
}

response = handler(event, {})

print(response)
