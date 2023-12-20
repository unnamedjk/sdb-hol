# Main Demo Launcher Form
import ipywidgets as widgets
from IPython.display import display, HTML
from IPython.display import display, clear_output

# Styling
style = {'description_width': 'initial'}
color = '#820ddf'
layout = widgets.Layout(width='30%')
layout = widgets.Layout(width='30%', display='flex', flex_flow='row', justify_content='space-between')

# Inputs
## Meta-data Inputs
owner_email    = widgets.Text(description='Email:', style=style, layout=layout)
demo_purpose   = widgets.Text(description='Demo Purpose:', style=style, layout=layout)
opportunity_id = widgets.Text(description='Opportunity ID:', style=style, layout=layout)

## SingleStore Inputs
sdb_api_key = widgets.Password(description='SDB Management API Key:', style=style, layout=layout)

## AWS Credentials Inputs
aws_creds_input = widgets.Textarea(
    description='AWS Credentials:',
    placeholder='Paste your credentials here...',
    style=style,
    layout=layout
)
aws_default_region = widgets.Text(description='AWS Default Region:', style=style, value="us-east-1", layout=layout)

# Buttons & Toggles
set_metadata_button = widgets.Button(description='Set Metadata', button_style='success', style={'button_color': color})
set_metadata_button.on_click(set_metadata)

# Update Credentials Button
update_creds_button = widgets.Button(description='Set AWS Creds', button_style='success', style={'button_color': color})
update_creds_button.on_click(update_aws_creds)

# Template Dropdown
template_url = "https://raw.githubusercontent.com/unnamedjk/stacks/main/stacks.yaml"
template_options = [('Select Template', None)] + fetch_yaml_content(template_url)[0]  # Only use the first element (list of tuples)
template = widgets.Dropdown(options=template_options, description='Template:', disabled=True, style=style, layout=layout)
template.observe(update_form_fields, names='value')

# Launch Demo Button
launch_demo_button = widgets.Button(description='Launch Demo', button_style='success', disabled=True, style={'button_color': color})
launch_demo_button.on_click(handle_create_stack)

# Add Workspace Button
add_workspace_button = widgets.Button(description='Add Workspace', button_style='info', style={'button_color': color}, disabled=True)
add_workspace_button.on_click(add_workspace)

# Create Workspace Button
create_sdb_button = widgets.Button(description='Create Workspace', button_style='success', disabled=True, style={'button_color': color})
create_sdb_button.on_click(None)

# Debug Checkbox
debug_toggle = widgets.Checkbox(
    value=False,
    description='Debug Mode',
    disabled=False,
    tooltip='Enable or disable debug mode'
)

# Stack Parameters
ssh_key_name = widgets.Text(description='SSH Key Name:', disabled=True, style=style, layout=layout)
ssh_key_name_tooltip = create_tooltip("Enter the name of your SSH Key")
demo_ttl = widgets.IntSlider(value=1, min=1, max=12, description='Demo TTL:', disabled=True, style=style, layout={'background_color': color})
demo_ttl_tooltip = create_tooltip("Select the Time-To-Live for the demo in hours")

# Tooltips
aws_default_region_tooltip = create_tooltip("Enter your AWS Default Region")
template_tooltip = create_tooltip("Select the Time-To-Live for the demo in hours")
aws_creds_tooltip = create_tooltip("Enter your AWS Environment variables here")
create_sdb_tooltip = create_tooltip("Create the above workspace group and workspaces")
sdb_api_key_tooltip = create_tooltip("Enter the SingleStore Management API Key here")

# Layout
# 
owner_email.layout = layout
demo_purpose.layout = layout
opportunity_id.layout = layout
sdb_api_key.layout = layout
aws_creds_input.layout = layout
aws_default_region.layout = layout

# Metadata Section
metadata_section = widgets.VBox(
    [
        widgets.HTML('<h2>Demo Metadata</h2>'),
        owner_email,
        demo_purpose,
        opportunity_id,
        set_metadata_button
    ],
    layout=widgets.Layout(margin='0 0 20px 0')
)
about_text = widgets.HTML('''
<p>
Welcome to the SingleStore Hands-On Labs Launcher.
In this form you will be able to choose from a selection of automated lab deployments that are designed to specifically give you a jump start with in SingleStore.
Please be sure to follow the form carefully and ensure you are watching the output section for the status of the lab being created. 
This form will automatically provision the following for you:
</p>
<ul>
    <li>All required AWS VPC, Security Group, Internet Gateways, and EC2 Instances</li>
    <li>All required SingleStore workspaces</li>
    <li>All required schema definitions for you to use the manual</li>
</ul>   
''')
# Credentials Section
credentials_section = widgets.VBox([
    widgets.HTML('<h2>Credentials</h2>'),
    widgets.HTML('<a style="color:#820ddf" href="https://memsql.atlassian.net/wiki/spaces/CLOUDINFRA/pages/2661023809/AWS+IIC+-+How+to+login">Please see the following JIRA for how to access AWS IIC</a>'),
    widgets.HTML('<a style="color:#820ddf" href="https://docs.singlestore.com/cloud/reference/management-api/">To obtain a SingleStore Management API Key, checkout our documentation</a>'),
    #debug_toggle,
    widgets.HBox([aws_creds_input, aws_creds_tooltip]),
    widgets.HBox([aws_default_region, aws_default_region_tooltip]),
    widgets.HBox([sdb_api_key, sdb_api_key_tooltip]),
    update_creds_button
], layout=widgets.Layout(margin='0 0 20px 0'))

# AWS Cloudformation Template Section
workspace_box = widgets.VBox([])
cloudformation_section = widgets.VBox(
    [
        widgets.HTML('<h2>Demo Launcher</h2>'),
        widgets.HBox([template, template_tooltip]),
        widgets.HTML('<h3>Demo Options</h2>'),
        widgets.HBox([ssh_key_name, ssh_key_name_tooltip]),
        widgets.HBox([demo_ttl, demo_ttl_tooltip]),
        widgets.HTML('<b>Workspace Details</b>'),
        workspace_box,
        add_workspace_button,
        launch_demo_button
    ],
    layout=widgets.Layout(margin='0 0 20px 0')
)

# SingleStore Section
singlestore_section = widgets.VBox(
    [
        widgets.HTML('<h2>SingleStore API Key</h2>'),
        sdb_api_key
    ],
    layout=widgets.Layout(margin='0 0 20px 0')
)

# Display form
form = widgets.VBox(
    [
        widgets.HTML('<h1>SingleStore Hands-On Labs Launcher</h1>'),
        about_text,
        metadata_section,
        credentials_section,
        cloudformation_section,
        widgets.HTML('<b>Output</b>'),
        output
    ],
    layout=widgets.Layout(margin='20px')
)
display(form)

# apiToken = "9ef9d49e7d01d894e4a78920493fbc01f7cc5ec4365f03472b3aefdc1a893c3d"