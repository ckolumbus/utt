import os

from ...api import _v1


class AzdoWiQuery:
    def __init__(self):
        self._wit_client = None

        try:
            # Fill in with your personal access token and org URL
            personal_access_token = os.environ["AZDO_PAT"]
            organization_url = os.environ["AZDO_URL"]

            from azure.devops.connection import Connection
            from msrest.authentication import BasicAuthentication

            # Create a connection to the org
            credentials = BasicAuthentication("PAT", personal_access_token)
            connection = Connection(base_url=organization_url, creds=credentials)

            # Get a client (the "core" client provides access to projects, teams, etc)
            self._wit_client = connection.clients.get_work_item_tracking_client()

        except KeyError:
            print("AzureDevOp not connected: set the AZDO_{PAT,URL} env var to a your Personal Access Token and URL")

    def _format_work_item(self, work_item):
        return "{0}: {2}".format(
            work_item.fields["System.WorkItemType"], work_item.id, work_item.fields["System.Title"],
        )

    def get_work_item(self, id: int) -> str:
        try:
            return self._format_work_item(self._wit_client.get_work_item(id))
        except:
            return ""


_v1.register_component(AzdoWiQuery, AzdoWiQuery)
