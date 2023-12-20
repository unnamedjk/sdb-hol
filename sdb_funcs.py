from datetime import datetime
import requests
import ipywidgets as widgets

class WorkspaceGroup:
    def __init__(self, apiToken, payload, output_widget):
        self.apiToken = apiToken
        self.payload = payload
        self.output_widget = output_widget
        self.apiHeaders = {"Accept": "application/json", "Authorization": f"Bearer {self.apiToken}"}
        self.apiUrl = "https://api.singlestore.com"
        self.apiRegionsUrl = f"{self.apiUrl}/v1/regions"
        self.apiWorkspaceGroupsUrl = f"{self.apiUrl}/v1/workspaceGroups"
        self.apiWorkspacesUrl = f"{self.apiUrl}/v1/workspaces"
        self.workspaceGroupID = None

    def log(self, message):
        with self.output_widget:
            print(f"{datetime.now()} - {message}")

    def _get_region_id(self, region_name):
        try:
            response = requests.get(self.apiRegionsUrl, headers=self.apiHeaders)
            if response.status_code == 200:
                for region in response.json():
                    if region['region'].lower() == region_name.lower():
                        return region['regionID']
            raise Exception(f"Region '{region_name}' not found")
        except Exception as e:
            self.log(f"Error getting region ID: {e}")
            raise

    def find_workspace_group(self):
        try:
            response = requests.get(self.apiWorkspaceGroupsUrl, headers=self.apiHeaders)
            if response.status_code == 200:
                for group in response.json():
                    if group['name'] == self.payload["name"]:
                        return group['workspaceGroupID']
            return None
        except Exception as e:
            self.log(f"Error finding workspace group: {e}")
            raise

    def create_workspace_group(self):
        try:
            self.log(f"Creating workspace group")
            existing_group_id = self.find_workspace_group()
            if existing_group_id:
                self.workspaceGroupID = existing_group_id
                self._wait_for_workspace_group_active()
                self.log("Workspace group already exists")
                return

            region_id = self._get_region_id(self.payload['regionName'])
            group_payload = {
                "adminPassword": self.payload["adminPassword"],
                "allowAllTraffic": self.payload["allowAllTraffic"],
                "expiresAt": self.payload["expiresAt"],
                "firewallRanges": self.payload["firewallRanges"],
                "name": self.payload["name"],
                "regionID": region_id,
                "updateWindow": self.payload["updateWindow"],
            }

            response = requests.post(self.apiWorkspaceGroupsUrl, headers=self.apiHeaders, json=group_payload)
            if response.status_code in [200, 201]:
                self.workspaceGroupID = response.json()['workspaceGroupID']
                self._wait_for_workspace_group_active()
                self.log("Workspace group created/identified successfully.")
            else:
                raise Exception(f"Failed to create workspace group: {response.text}")
        except Exception as e:
            self.log(f"Error creating workspace group: {e}")
            raise

    def _wait_for_workspace_group_active(self):
        try:
            timeout = 600  # Timeout after 300 seconds (5 minutes)
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < timeout:
                self.log(f"Waiting for workspace group {self.workspaceGroupID} to be ACTIVE")
                response = requests.get(f"{self.apiWorkspaceGroupsUrl}/{self.workspaceGroupID}", headers=self.apiHeaders)
                if response.status_code == 200 and response.json()['state'] == 'ACTIVE':
                    self.log("Workspace group is now active.")
                    return
                time.sleep(5)
            raise TimeoutError("Timed out waiting for workspace group to become active.")
        except Exception as e:
            self.log(f"Error during wait for workspace group: {e}")
            raise

    def create_workspaces(self):
        try:
            if self.workspaceGroupID is None:
                self.create_workspace_group()

            created_workspaces = []
            for ws in self.payload['workspaces']:
                workspace_id = self.find_workspace(ws['name'])
                if workspace_id:
                    self._wait_for_workspace_active(workspace_id)
                    created_workspaces.append({'workspaceID': workspace_id, 'name': ws['name']})
                else:
                    ws_payload = {**ws, "workspaceGroupID": self.workspaceGroupID}
                    response = requests.post(self.apiWorkspacesUrl, headers=self.apiHeaders, json=ws_payload)
                    if response.status_code == 200:
                        workspace_id = response.json()['workspaceID']
                        self._wait_for_workspace_active(workspace_id)
                        created_workspaces.append(response.json())
                    else:
                        raise Exception(f"Failed to create workspace: {response.text}")
            self.log("Workspaces created successfully.")
            return created_workspaces
        except Exception as e:
            self.log(f"Error creating workspaces: {e}")
            raise

    def _wait_for_workspace_active(self, workspace_id):
        try:
            timeout = 600  # Timeout after 300 seconds (5 minutes)
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < timeout:
                self.log(f"Waiting for workspace {workspace_id} to be ACTIVE")
                response = requests.get(f"{self.apiWorkspacesUrl}/{workspace_id}", headers=self.apiHeaders)
                if response.status_code == 200 and response.json()['state'] == 'ACTIVE':
                    self.log(f"Workspace {workspace_id} is now active.")
                    return
                time.sleep(5)
            raise TimeoutError(f"Timed out waiting for workspace {workspace_id} to become active.")
        except Exception as e:
            self.log(f"Error during wait for workspace {workspace_id}: {e}")
            raise

    def _construct_mongo_endpoint(self, endpoint_url):
        try:
            mongo_host = endpoint_url.replace("-dml.", "-mongo.") + ":27017"
            mongo_conn_str = f"mongodb://{self.payload['adminUsername']}:{self.payload['adminPassword']}@{mongo_host}/?authMechanism=PLAIN&tls=true&loadBalanced=true"
            return mongo_conn_str
        except Exception as e:
            self.log(f"Error constructing MongoDB endpoint: {e}")
            raise

    def get_workspace_details(self):
        try:
            self.log("Obtaining workspace details")
            if self.workspaceGroupID is None:
                raise Exception("Workspace group is not created")

            workspaces = self.list_workspaces()
            if not workspaces:
                raise Exception("No workspaces found")

            details = {}
            for workspace in workspaces:
                endpoint_url = workspace['endpoint']
                mongo_endpoint = self._construct_mongo_endpoint(endpoint_url)
                details[workspace['name']] = {
                    'endpoint_url': endpoint_url,
                    'mongo_endpoint': mongo_endpoint,
                    'username': self.payload['adminUsername'],
                    'password': self.payload['adminPassword'],
                }
            self.log("Workspace details fetched successfully.")
            return details
        except Exception as e:
            self.log(f"Error getting workspace details: {e}")
            raise

    def list_workspaces(self):
        try:
            response = requests.get(f"{self.apiWorkspacesUrl}?workspaceGroupID={self.workspaceGroupID}", headers=self.apiHeaders)
            if response.status_code == 200:
                self.log("Workspaces listed successfully.")
                return response.json()
            else:
                raise Exception("Failed to list workspaces")
        except Exception as e:
            self.log(f"Error listing workspaces: {e}")
            raise

    def find_workspace(self, workspace_name):
        try:
            self.log(f"Attempting to find workspace {workspace_name}")
            response = requests.get(f"{self.apiWorkspacesUrl}?workspaceGroupID={self.workspaceGroupID}", headers=self.apiHeaders)
            if response.status_code == 200:
                for workspace in response.json():
                    if workspace['name'] == workspace_name:
                        self.log(f"Workspace '{workspace_name}' found with ID {workspace['workspaceID']}.")
                        return workspace['workspaceID']
                self.log(f"Workspace '{workspace_name}' not found.")
                return None
            else:
                raise Exception(f"Failed to retrieve workspaces for workspaceGroupID {self.workspaceGroupID}")
        except Exception as e:
            self.log(f"Error finding workspace '{workspace_name}': {e}")
            raise