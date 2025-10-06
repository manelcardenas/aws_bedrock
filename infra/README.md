
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!




TODO:
- name: 🔐 Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4  # Better than env vars
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: eu-west-3

- name: ✅ Verify AWS credentials
      run: aws sts get-caller-identity


- name: 💾 Backup current stack
      working-directory: ./infra
      run: |
        echo "💾 Creating backup of current stack..."
        aws cloudformation describe-stacks \
          --stack-name InfraStack \
          --query 'Stacks[0]' > stack-backup-$(date +%Y%m%d-%H%M%S).json \
          || echo "⚠️ No existing stack to backup"
      continue-on-error: true  # Don't fail if stack doesn't exist yet

        
- name: 🚀 Deploy to Production
    working-directory: ./infra
    run: |
    echo "🚀 Deploying text summary to production..."
    cdk deploy --require-approval never
    
- name: ✅ Deployment Success
    if: success()
    run: echo "✅ Text summary deployment complete!"
    
- name: ❌ Deployment Failed
    if: failure()
    run: |
    echo "❌ Deployment failed! Check logs for details."
    echo "🔄 Consider manual rollback if needed"
    exit 1