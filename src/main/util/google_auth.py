import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleAuth:

    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.events', 'https://www.googleapis.com/auth/calendar.readonly',
                       'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

    def authenticate(self):
        current_file_directory = os.path.dirname(__file__)
        src_directory = os.path.abspath(os.path.join(current_file_directory, '..', '..'))
        resources_path = os.path.join(src_directory, 'resources')
        creds = None
        if os.path.exists(os.path.join(resources_path, 'token.json')):
            creds = Credentials.from_authorized_user_file(os.path.join(resources_path, 'token.json'), self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.join(resources_path, "credentials.json"), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(os.path.join(resources_path, 'token.json'), "w") as token:
                token.write(creds.to_json())
        return creds
