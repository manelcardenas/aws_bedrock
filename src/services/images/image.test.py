import json
from image import handler

event = {
    "body": json.dumps({"description": "A photo of a cat"}),
}

response = handler(event, {})

print(response)
