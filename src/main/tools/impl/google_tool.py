import base64
import os
from email.message import EmailMessage

from flask import current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request


class GoogleTool:

    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.events',
                       'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
        self.credentials = self.authenticate()
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
        self.gmail_service = build("gmail", "v1", credentials=self.credentials)

    def authenticate(self):
        current_file_directory = os.path.dirname(__file__)
        src_directory = os.path.abspath(os.path.join(current_file_directory, '..', '..', '..'))
        resources_path = os.path.join(src_directory, 'resources')
        if os.path.exists(os.path.join(resources_path, 'token.json')):
            creds = Credentials.from_authorized_user_file(os.path.join(resources_path, 'token.json'), self.SCOPES)
        else:
            raise FileNotFoundError("token.json not found")
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

    def send_email(self, contact_emails, subject, email_body):
        # Compose the email
        message = EmailMessage()
        message["To"] = ", ".join(contact_emails)
        message["From"] = current_app.config['SENDER_EMAIL']
        message["Subject"] = subject
        message.set_content(email_body)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}

        try:
            send_message = (
                self.gmail_service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            print(f'Message Id: {send_message["id"]}')
            print("Email sent successfully!")
        except HttpError as error:
            print(f"An error occurred: {error}")

    # Gmail API function to find recipient emails by name
    def find_email_by_name(self, name):
        try:
            # Use Gmail API to search for the user by name (adjust this query to fit your data format)
            query = f"to:{name}"
            results = self.gmail_service.users().messages().list(userId='me', q=query).execute()
            if 'messages' in results:
                message = self.gmail_service.users().messages().get(userId='me', id=results['messages'][0]['id']).execute()
                headers = message['payload']['headers']
                email = next((header['value'] for header in headers if header['name'] == 'To'), None)
                return email
        except Exception as e:
            print("Error finding email:", e)
        return None

    def create_event(self, event_payload):
        event_result = self.calendar_service.events().insert(calendarId='primary', body=event_payload).execute()
        return event_result
