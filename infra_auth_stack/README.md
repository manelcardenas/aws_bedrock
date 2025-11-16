# 🔐 Authentication & Proxy Stack

# Welcome to your CDK Python project!

Authentication layer for AWS Bedrock Playground that protects your existing Image and Text APIs with JWT-based authentication.

This is a blank project for CDK development with Python.

## 📋 Overview

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This CDK stack creates an authentication proxy that:

- Validates user credentials against DynamoDBThis project is set up like a standard Python project. The initialization

- Issues JWT tokens for authenticated usersprocess also creates a virtualenv within this project, stored under the `.venv`

- Forwards authenticated requests to your existing APIsdirectory. To create the virtualenv it assumes that there is a `python3`

- **Hides API keys from the frontend** (stored in Lambda environment)(or `python` for Windows) executable in your path with access to the `venv`

package. If for any reason the automatic creation of the virtualenv fails,

## 🏗️ Architectureyou can create the virtualenv manually.

````To manually create a virtualenv on MacOS and Linux:

Frontend → Auth API Gateway → Auth Lambda → DynamoDB (login)

                            → Proxy Lambda → Existing Image/Text APIs (protected)```

```$ python3 -m venv .venv

````

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed flow diagrams.

After the init process completes and the virtualenv is created, you can use the following

## 🚀 Quick Startstep to activate your virtualenv.

### Prerequisites```

- AWS CLI configured$ source .venv/bin/activate

- AWS CDK installed```

- Docker running (for Lambda bundling)

- Your existing Image and Text APIs deployedIf you are a Windows platform, you would activate the virtualenv like this:

### 1. Setup```

````bash% .venv\Scripts\activate.bat

# Install dependencies```

pip install -r requirements.txt

Once the virtualenv is activated, you can install the required dependencies.

# Copy and configure environment variables

cp .env.example .env```

nano .env  # Add your JWT_SECRET and API keys$ pip install -r requirements.txt

````

### 2. DeployAt this point you can now synthesize the CloudFormation template for this code.

````bash

cdk deploy```

```$ cdk synth

````

### 3. Add Users

````bashTo add additional dependencies, for example other CDK libraries, just add

python3 manage_users.py add --username testuser --password test123them to your `setup.py` file and rerun the `pip install -r requirements.txt`

```command.



### 4. Test## Useful commands

```bash

# Login * `cdk ls`          list all stacks in the app

curl -X POST https://YOUR-API/prod/login \ * `cdk synth`       emits the synthesized CloudFormation template

  -H "Content-Type: application/json" \ * `cdk deploy`      deploy this stack to your default AWS account/region

  -d '{"username":"testuser","password":"test123"}' * `cdk diff`        compare deployed stack with current state

 * `cdk docs`        open CDK documentation

# Use JWT token for protected endpoints

curl -X POST https://YOUR-API/prod/proxy/image \Enjoy!

  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"A sunset"}'
````

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture diagrams

## 📁 Project Structure

```
infra_auth_stack/
├── services/
│   ├── auth.py              # Lambda functions (login_handler, proxy_handler)
│   └── requirements.txt     # Lambda dependencies (PyJWT, requests)
├── infra_auth_stack/
│   └── infra_auth_stack_stack.py  # CDK stack definition
├── app.py                   # CDK app entry point
├── manage_users.py          # User management CLI
├── .env.example             # Environment variables template
└── .env                     # Your secrets (NEVER commit!)
```

## 🔒 Security

- JWT tokens expire after 24 hours
- API keys stored in Lambda environment (hidden from frontend)
- Passwords hashed with SHA-256
- User-specific authentication

⚠️ **Important**: Never commit `.env` file to version control!

## 🛠️ Configuration

Edit `.env` with your values:

```bash
JWT_SECRET=<generate-random-string>
IMAGE_API_URL=https://your-image-api.../prod/image
IMAGE_API_KEY=<your-image-api-key>
TEXT_API_URL=https://your-text-api.../prod/text
TEXT_API_KEY=<your-text-api-key>
```

## 📤 Outputs After Deployment

- `UsersTableName` - DynamoDB table name
- `LoginEndpoint` - POST /login (public)
- `ImageProxyEndpoint` - POST /proxy/image (JWT required)
- `TextProxyEndpoint` - POST /proxy/text (JWT required)

## 🧹 Cleanup

```bash
cdk destroy
```

## 💡 CDK Commands

- `cdk synth` - Generate CloudFormation template
- `cdk deploy` - Deploy to AWS
- `cdk diff` - Show changes
- `cdk destroy` - Delete all resources

## 📞 Troubleshooting

Check Lambda logs:

```bash
aws logs tail /aws/lambda/prod-auth-lambda-ACCOUNT_ID --follow --region eu-west-3
aws logs tail /aws/lambda/prod-proxy-lambda-ACCOUNT_ID --follow --region eu-west-3
```

Common issues:

- **"No module named 'jwt'"** - Ensure Docker is running for Lambda bundling
- **"Invalid credentials"** - Check user exists: `python3 manage_users.py list`
- **"Failed to call backend API"** - Verify API URLs in `.env` are correct

---

**Region**: `eu-west-3` (configured in `app.py`)  
**Environment**: `prod`
