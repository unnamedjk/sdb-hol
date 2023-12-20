# Main Form Functions
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
from datetime import datetime

# Logging
output = widgets.Output()

# Global Variables
generated_name   = None
owner_email_str  = None
demo_purpose_str = None

def set_metadata(sender):
    global owner_email_str, demo_purpose_str
    if owner_email_str == None:
        owner_email_str == owner_email.value
    if demo_purpose_str == None:
        demo_purpose_str = demo_purpose.value
    msg = "Updated metadata"
    with output:
        print(f'{datetime.now()} - {msg}')

def generate_lab_name(template_name, owner_email):
    global generated_name, owner_email_str
    if generated_name is None:
        email_str = owner_email.value
        email_prefix = email_str.split('@')[0].replace('.', '')
        name_part = template_name.split()[0].lower()
        timestamp = int(time.time())
        generated_name = f"{email_prefix}-{name_part}-{timestamp}"
    with output:
        msg = f"Generated the lab name: {generated_name}"
        print(f"{datetime.now()} - {msg}")

    return generated_name

# Define custom tag handlers
def ref_constructor(loader, node):
    return {'Ref': loader.construct_scalar(node)}

def getatt_constructor(loader, node):
    return {'Fn::GetAtt': loader.construct_scalar(node).split('.')}

def sub_constructor(loader, node):
    return {'Fn::Sub': loader.construct_scalar(node)}

class CustomSafeLoader(yaml.SafeLoader):
    pass

# Add constructors for CloudFormation tags
CustomSafeLoader.add_constructor('!Ref', ref_constructor)
CustomSafeLoader.add_constructor('!GetAtt', getatt_constructor)
CustomSafeLoader.add_constructor('!Sub', sub_constructor)

# Custom loader that ignores unrecognized tags
class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
    def ignore_unknown_tags(self, node):
        return None

SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown_tags)

# Yaml Fetchers
# Function to fetch and parse the stacks.yaml & CloudFormation template
def fetch_yaml_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = yaml.load(response.text, Loader=CustomSafeLoader)  # Use CustomSafeLoader
            if 'stacks' in data:
                templates = [(stack['name'], stack['url']) for stack in data['stacks']]
                with output:
                    msg = f"Successfully returned {len(templates)} templates"
                return templates, None
            else:
                with output:
                    msg = "No 'stacks' key found in YAML"
                    print(f"{datetime.now} - {msg}")
                return []
        else:
            return [], f"Failed to fetch the template: HTTP {response.status_code}"
    except yaml.YAMLError as e:
        return [], f"Error parsing YAML: {e}"

def fetch_stack_yaml_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = yaml.load(response.text, Loader=CustomSafeLoader)  # Use CustomSafeLoader
            if 'Parameters' in data:
                return data['Parameters']
            else:
                with output:
                    msg = "No 'Parameters' key found in stack YAML"
                    print(f"{datetime.now()} - {msg}")
                return None
        else:
            with output:
                msg = f"Failed to fetch the stack template: HTTP {response.status_code}"
                print(f"{datetime.now()} - {msg}")
            return None
    except yaml.YAMLError as e:
        with output:
            msg = f"Error parsing stack YAML: {e}"
            print(f"{datetime.now()} - {msg}")
        return None

# Form Utilities
# Helper function to create a tooltip
def create_tooltip(text):
    return widgets.HTML(value=f'<span title="{text}">?</span>')

# Function to enable inputs after successful AWS credential update
def enable_inputs():
    template.disabled = False
    add_workspace_button.disabled = False

# Function to enable demo launcher section after setting AWS credentials
def enable_demo_launcher():
    template.disabled = False
    ssh_key_name.disabled = False
    demo_ttl.disabled = False

# Function to enable workspace details after creating the stack
def enable_workspace_details(sender):
    add_workspace_button.disabled = False
    for child in workspace_box.children:
        for widget in child.children:
            widget.disabled = False

# Form field updater based on dynamic content from yaml
def update_form_fields(change):
    if change['new']:
        stack_url = change['new']
        if stack_url:
            parameters = fetch_stack_yaml_content(stack_url)
            if parameters:
                with output:
                    msg = "Fetched Parameters:", parameters
                if 'KeyName' in parameters:
                    ssh_key_name.value = parameters['KeyName'].get('Default', '')
                if 'TTL' in parameters:
                    demo_ttl.value = int(parameters['TTL'].get('Default', 1))
                if 'WorkspaceDetails' in parameters:
                    workspace_details_str = parameters['WorkspaceDetails'].get('Default', '{}')
                    try:
                        workspace_details = json.loads(workspace_details_str)
                        if 'workspaces' in workspace_details:  # Ensure 'workspaces' key is in the JSON
                            workspace_widgets = create_workspace_widgets(workspace_details['workspaces'])
                            workspace_box.children = tuple(workspace_widgets)
                        else:
                            with output:
                                msg = "No 'workspaces' key found in WorkspaceDetails."
                                print(f"{datetime.now()} - {msg}")
                    except json.JSONDecodeError:
                        with output:
                            msg = "WorkspaceDetails JSON parsing error."
                            print(f"{datetime.now()} - {msg}")
            else:
                with output:
                    msg = "No parameters found in the selected template."
                    print(f"{datetime.now()} - {msg}")
        else:
            with output:
                msg = "No URL found for the selected template."
                print(f"{datetime.now()} - {msg}")
    else:
        with output:
            msg = "Invalid template selection."
            print(f"{datetime.now()} - {msg}")
    launch_demo_button.disabled = False

# SingleStore Form Functions
# Function to create workspace widgets
def create_workspace_widgets(workspace_json):
    workspace_widgets = []

    # Define the layout for the widgets
    label_layout = widgets.Layout(width='150px')
    text_layout = widgets.Layout(width='150px')
    dropdown_layout = widgets.Layout(width='150px')
    checkbox_layout = widgets.Layout(width='150px')

    # Create headers for the table
    headers = [
        widgets.Label('Workspace Name', layout=label_layout),
        widgets.Label('Workspace Size', layout=label_layout),
        widgets.Label('Enable Kai', layout=label_layout)
    ]
    workspace_widgets.append(widgets.HBox(headers))

    # Define possible sizes
    possible_sizes = ['S-00', 'S-0', 'S-1', 'S-2', 'S-4', 'S-6', 'S-8', 'S-12', 'S-16', 'S-20', 'S-24', 'S-28']

    # Create a row for each workspace
    for workspace in workspace_json:
        name = workspace.get('name', 'Unknown')
        size = workspace.get('size', 'S-00')
        enable_kai = workspace.get('enableKai', False)

        name_widget = widgets.Text(
            value=name,
            description='',
            disabled=False,
            layout=text_layout
        )

        size_widget = widgets.Dropdown(
            options=possible_sizes,
            value=size if size in possible_sizes else '00',
            description='',
            disabled=False,
            layout=dropdown_layout
        )

        enable_kai_widget = widgets.Checkbox(
            value=enable_kai,
            description='',
            disabled=False,
            layout=checkbox_layout
        )

        row = widgets.HBox([name_widget, size_widget, enable_kai_widget])
        workspace_widgets.append(row)

    return workspace_widgets

# Function to add a new workspace
def add_workspace(b):
    # Define default values for a new workspace
    default_name = ''  # You can set a default name or leave it empty
    default_size = 'S-00'  # Default size, adjust as needed
    default_enable_kai = False  # Default value for Enable Kai

    # Define possible sizes (ensure this matches with the list in create_workspace_widgets)
    possible_sizes = ['S-00', 'S-0', 'S-1', 'S-2', 'S-4', 'S-6', 'S-8', 'S-12', 'S-16', 'S-20', 'S-24', 'S-28']

    # Define the layout for the widgets
    text_layout = widgets.Layout(width='150px')
    dropdown_layout = widgets.Layout(width='150px')
    checkbox_layout = widgets.Layout(width='150px')

    # Create widgets for the new workspace
    name_widget = widgets.Text(
        value=default_name,
        description='',
        disabled=False,
        layout=text_layout
    )

    size_widget = widgets.Dropdown(
        options=possible_sizes,
        value=default_size,
        description='',
        disabled=False,
        layout=dropdown_layout
    )

    enable_kai_widget = widgets.Checkbox(
        value=default_enable_kai,
        description='',
        disabled=False,
        layout=checkbox_layout
    )

    # Create a new row and append it to the existing widgets
    new_row = widgets.HBox([name_widget, size_widget, enable_kai_widget])
    workspace_box.children += (new_row,)
