# AWS Functions
import requests
import yaml
import json
import uuid
import re
import boto3
import time
from botocore.exceptions import ClientError
import ipywidgets as widgets
from IPython.display import display, clear_output
from datetime import datetime, timedelta

# Global variables to store AWS credentials
global_aws_access_key = None
global_aws_secret_key = None
global_aws_session_token = None

# Function to update AWS credentials
def update_aws_creds(sender):
    global global_aws_access_key, global_aws_secret_key, global_aws_session_token

    creds_text = aws_creds_input.value
    try:
        # Extract credentials using regular expressions
        access_key_match = re.search(r"AWS_ACCESS_KEY_ID=\"([^\"]+)\"", creds_text)
        secret_key_match = re.search(r"AWS_SECRET_ACCESS_KEY=\"([^\"]+)\"", creds_text)
        session_token_match = re.search(r"AWS_SESSION_TOKEN=\"([^\"]+)\"", creds_text)

        if access_key_match and secret_key_match and session_token_match:
            global_aws_access_key = access_key_match.group(1)
            global_aws_secret_key = secret_key_match.group(1)
            global_aws_session_token = session_token_match.group(1)

            # Validate credentials (optional)
            if validate_aws_credentials(global_aws_access_key, global_aws_secret_key, global_aws_session_token):
                msg = "AWS Credentials Updated and Validated Successfully"
                with output:
                    print(f"{datetime.now()} - {msg}")
                    enable_demo_launcher()
            else:
                msg = "AWS Credentials Invalid"
                with output:
                    print(f"{datetime.now()} - {msg}")
                enable_demo_launcher()
        else:
            with output:
                msg = "Error parsing AWS credentials. Please check the format."
                print(f"{datetime.now()} - {msg}")
    except Exception as e:
        with output:
            msg = f"Error updating AWS credentials: {e}"
            print(f"{datetime.now()} - {msg}")

# Function for validating AWS Credentials
def validate_aws_credentials(access_key, secret_key, session_token):
    try:
        # Attempt to create a boto3 client with the provided credentials
        client = boto3.client(
            'sts',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token
        )
        # Call GetCallerIdentity to validate credentials
        client.get_caller_identity()
        with output:
            msg = "Successfully authenticated to AWS"
            print(f"{datetime.now()} - {msg}")
        return True
    except Exception as e:
        with output:
            msg = f"Error validating AWS credentials: {e}"
            print(f"{datetime.now()} - {msg}")
        return False

def handle_create_stack(b):
    global global_aws_access_key, global_aws_secret_key, global_aws_session_token, generated_name, owner_email_str
    if generated_name == None:
        selected_template_name = template.label
        generated_name = generate_lab_name(selected_template_name, owner_email)
    
    # Fetch and parse stack.yaml content
    stack_url = template.value
    stack_parameters = fetch_stack_yaml_content(stack_url)
    if stack_parameters and 'WorkspaceDetails' in stack_parameters:
        workspace_details_from_template = stack_parameters['WorkspaceDetails'].get('Default', '{}')
        workspaces_payload = json.loads(workspace_details_from_template)

        # Building the payload for SingleStore workspace
        ttl = datetime.now() + timedelta(hours=demo_ttl.value)
        formatted_time = ttl.isoformat()
        workspace_payload = {
            "adminUsername": "admin",
            "adminPassword": "SingleStore1",
            "allowAllTraffic": True,
            "expiresAt": formatted_time,
            "firewallRanges": ["192.168.0.1/32", "192.168.0.81/12", "50.68.208.146/32"],
            "name": generated_name,
            "regionName": "US East 1 (N. Virginia)",
            "updateWindow": {"day": 2, "hour": 1},
            "workspaces": workspaces_payload['workspaces']
        }

        # Create SingleStore Workspace Group
        workspace_group = WorkspaceGroup(sdb_api_key.value, workspace_payload, output)
        workspace_group.create_workspace_group()
        workspace_group.create_workspaces()
        singlestore_details = workspace_group.get_workspace_details()
        
        # Convert SingleStore details to JSON string for CloudFormation parameter
        singlestore_conn_details = json.dumps(singlestore_details)

        # Fetch CloudFormation template body
        response = requests.get(stack_url)
        if response.status_code != 200:
            msg = f"Failed to fetch the CloudFormation template: HTTP {response.status_code}"
            with output:
                print(f"{datetime.now()} - {msg}")
            return

        template_body = response.text

        # Create CloudFormation stack
        outputs = create_cloudformation_stack(
            generated_name,
            template_body,
            owner_email,
            singlestore_conn_details,
            global_aws_access_key,
            global_aws_secret_key,
            global_aws_session_token,
            aws_default_region.value
        )

        if outputs:
            msg = "Stack created successfully. Outputs:", outputs
            with output:
                print(f"{datetime.now()} - {msg}")
            
        else:
            msg = "Failed to create the stack."
            with output:
                print(f"{datetime.now()} - {msg}")
            
    else:
        with output:
            msg = "Invalid stack URL or missing WorkspaceDetails in stack.yaml."
            print(f"{datetime.now()} - {msg}")

# Function to create and handle CloudFormation stack
def create_cloudformation_stack(template_name, template_body, owner_email, singlestore_conn_details, aws_access_key, aws_secret_key, aws_session_token, region_name='us-east-1'):
    global owner_email_str
    #name_part = template_name.split()[0].lower()

    try:
        with output:
            msg = f"Setting up boto3 client session"
            print(f"{datetime.now()} - {msg}")

        # Create CloudFormation client
        cf_client = boto3.client(
            'cloudformation',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            aws_session_token=aws_session_token,
            region_name=region_name
        )

        # Define tags
        tags = [
            {'Key': 'ownerEmail', 'Value': owner_email.value},
            {'Key': 'templateName', 'Value': template_name}
        ]

        # Create the stack with the template body and parameters
        cf_client.create_stack(
            StackName=template_name,
            TemplateBody=template_body,
            Parameters=[
                {'ParameterKey': 'SingleStoreConnDetails', 'ParameterValue': singlestore_conn_details}
            ],
            Tags=tags
        )

        # Wait for the stack to be created
        with output:
            msg = f"Creating stack {template_name}. This may take a few minutes..."
            print(f"{datetime.now()} - {msg}")
        waiter = cf_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=template_name)

        # Fetch stack outputs
        stack_info = cf_client.describe_stacks(StackName=template_name)
        outputs = stack_info['Stacks'][0]['Outputs']
        with output:
            msg = f"Created stack {template_name}"
            print(f"{datetime.now()} - {msg}")

        return outputs
    except ClientError as e:
        with output:
            msg = f"An error occurred: {e}"
            print(f"{datetime.now()} - {msg}")
        return None