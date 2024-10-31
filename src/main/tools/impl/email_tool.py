from typing import Dict, Any

from langchain_core.tools import tool

class EmailTool:
    def __init__(self):
        self.api_key = None

    @tool
    def send_email(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Sends email to the recipients with the subject and the body
        :param recipient:
        :param subject:
        :param body:
        :return:
        """
        # Logic for sending email using an email API like Gmail API
        # Here we assume a successful response is returned for simplicity
        response = {"status": "success", "message": f"Email sent to {recipient}"}
        return response