import json
import os
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

# For JWT operations
import jwt

# For making HTTP requests to existing APIs
import requests


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗄️ DynamoDB Client
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dynamodb = boto3.resource("dynamodb")


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256
    In production, use bcrypt or argon2 instead!
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a password against its hash"""
    return hmac.compare_digest(stored_hash, hash_password(provided_password))


def generate_jwt(username: str, jwt_secret: str, expiration_hours: int = 24) -> str:
    """
    Generate a JWT token for authenticated user

    Token contains:
    - username: User identifier
    - exp: Expiration timestamp
    - iat: Issued at timestamp
    """
    now = datetime.utcnow()
    payload = {
        "username": username,
        "iat": now,
        "exp": now + timedelta(hours=expiration_hours),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def validate_jwt(token: str, jwt_secret: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token and return payload
    Returns None if invalid
    """
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {str(e)}")
        return None


def cors_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to create CORS-enabled responses"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,x-api-key",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔐 LAMBDA 1: LOGIN HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def login_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user login requests

    Expected request body:
    {
        "username": "john_doe",
        "password": "secret123"
    }

    Success response:
    {
        "token": "eyJhbGciOiJIUzI1NiIs...",
        "username": "john_doe",
        "expires_in": 86400
    }
    """
    print("🔐 Login request received")

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        username = body.get("username", "").strip()
        password = body.get("password", "")

        # Validation
        if not username or not password:
            return cors_response(400, {"error": "Username and password required"})

        # Get environment variables
        table_name = os.environ.get("USERS_TABLE")
        jwt_secret = os.environ.get("JWT_SECRET")
        jwt_expiration = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

        if not table_name or not jwt_secret:
            print("❌ Missing environment variables")
            return cors_response(500, {"error": "Server configuration error"})

        # Query DynamoDB
        table = dynamodb.Table(table_name)

        try:
            response = table.get_item(Key={"username": username})
        except ClientError as e:
            print(f"❌ DynamoDB error: {str(e)}")
            return cors_response(500, {"error": "Database error"})

        # Check if user exists
        if "Item" not in response:
            print(f"❌ User not found: {username}")
            return cors_response(401, {"error": "Invalid credentials"})

        user = response["Item"]
        stored_password_hash = user.get("password_hash", "")

        # Verify password
        if not verify_password(stored_password_hash, password):
            print(f"❌ Invalid password for user: {username}")
            return cors_response(401, {"error": "Invalid credentials"})

        # Generate JWT token
        token = generate_jwt(username, jwt_secret, jwt_expiration)

        print(f"✅ Login successful for user: {username}")

        return cors_response(
            200,
            {
                "token": token,
                "username": username,
                "expires_in": jwt_expiration * 3600,  # Convert hours to seconds
            },
        )

    except json.JSONDecodeError:
        return cors_response(400, {"error": "Invalid JSON in request body"})
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return cors_response(500, {"error": "Internal server error"})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 LAMBDA 2: PROXY HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def proxy_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Proxy requests to existing APIs after JWT validation

    This Lambda:
    1. Validates JWT token from frontend
    2. Adds API key (hidden from frontend!)
    3. Forwards request to existing API Gateway
    4. Returns response to frontend

    Endpoints:
    - POST /proxy/image → calls IMAGE_API_URL
    - POST /proxy/text → calls TEXT_API_URL
    """
    print("🔄 Proxy request received")

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 1: Extract and validate JWT token
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        auth_header = event.get("headers", {}).get("Authorization") or event.get(
            "headers", {}
        ).get("authorization", "")

        if not auth_header.startswith("Bearer "):
            return cors_response(
                401, {"error": "Missing or invalid Authorization header"}
            )

        token = auth_header.replace("Bearer ", "")
        jwt_secret = os.environ.get("JWT_SECRET")

        # Validate token
        payload = validate_jwt(token, jwt_secret)
        if not payload:
            return cors_response(401, {"error": "Invalid or expired token"})

        username = payload.get("username")
        print(f"✅ Valid JWT for user: {username}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2: Determine target API based on path
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        path = event.get("path", "")
        request_body = event.get("body", "{}")

        if "/image" in path:
            target_url = os.environ.get("IMAGE_API_URL")
            api_key = os.environ.get("IMAGE_API_KEY")
            endpoint_name = "image"

        elif "/text" in path:
            target_url = os.environ.get("TEXT_API_URL")
            api_key = os.environ.get("TEXT_API_KEY")
            endpoint_name = "text"

            # Add query parameters for text endpoint
            query_params = event.get("queryStringParameters", {})
            if query_params:
                query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
                target_url = f"{target_url}?{query_string}"
        else:
            return cors_response(404, {"error": "Unknown endpoint"})

        if not target_url or not api_key:
            print(f"❌ Missing configuration for {endpoint_name} API")
            return cors_response(500, {"error": "Backend configuration error"})

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 3: Call existing API with API key
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print(f"🔄 Forwarding to {endpoint_name} API: {target_url}")
        print(f"🔑 Using API key: {api_key[:10]}...")

        # Make HTTP request to existing API
        response = requests.post(
            target_url,
            headers={
                "x-api-key": api_key,  # The secret API key!
                "Content-Type": "application/json",
            },
            data=request_body,
            timeout=30,
        )

        print(f"✅ Response from {endpoint_name} API: {response.status_code}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 4: Return response to frontend
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        return {
            "statusCode": response.status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,x-api-key",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            },
            "body": response.text,
        }

    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return cors_response(504, {"error": "Request timeout"})
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling backend API: {str(e)}")
        return cors_response(500, {"error": "Failed to call backend API"})
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return cors_response(500, {"error": "Internal server error"})
