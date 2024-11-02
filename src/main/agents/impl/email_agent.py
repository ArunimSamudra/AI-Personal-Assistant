# # import ollama
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

import base64
from email.message import EmailMessage

from flask import current_app
from googleapiclient.errors import HttpError
from langchain_core.tools import tool
from googleapiclient.discovery import build

from main.config import Config
from main.util.google_auth import GoogleAuth


class EmailAgent:

    def __init__(self, model):
        self.email_prompt = f"""
                You are part of a multi-agent system designed to be a personal assistant for the user. 
                Specifically, you are the **Email Agent** responsible for composing and sending emails on behalf of the user.
                
                Your task is to gather three essential pieces of information needed to send an email:
                1. **Recipient(s)**: Who the email is for, i.e, their email id(s)
                2. **Body**: The main message of the email.
                3. **Subject**: A brief description of the email topic.
                
                Also, The sender's name is {Config.SENDER_NAME}, so don't ask that from the user
                
                Your responsibilities are as follows:
                - **Extract Information**: When the user requests an email, analyze their query to identify the 
                  recipients, body, and subject. If any of this information is missing or unclear, ask the user directly to provide it.
                  
                - **Draft Confirmation**: Once all required information is gathered, generate a draft email 
                  that includes the recipient(s), subject, and body. Display this draft to the user and explicitly 
                  ask for confirmation before sending. Your confirmation request should allow the user to review the email and verify its details.
                
                - **Send or Modify**: 
                    - If the user confirms, send the email on their behalf and inform them that it has been sent successfully.
                    - If the user does not confirm, ask for specific changes or suggestions on how to adjust the draft 
                     to better match their needs. Use the user’s feedback to update the draft and repeat the confirmation process until they approve.
                
                Additional Guidelines:
                - **Clarity and Professionalism**: Ensure the draft is clearly worded, professional, and accurate.
                - **Polite and Prompt**: When requesting missing information or asking for confirmation, be polite and 
                        concise to facilitate a smooth, user-friendly interaction.
                - **Iterative Approach**: Continue iterating through the steps of drafting and confirming until the user 
                    is satisfied and confirms the email draft for sending.
                
                Your goal is to streamline the email composition and confirmation process while ensuring that all 
                details are correct and aligned with the user’s intent.
                """
        self.email_agent = create_react_agent(model, tools=[self.extract_info_from_query, self.send_email],
                                              state_modifier=self.email_prompt)

    def __call__(self):
        return self.email_agent

    @staticmethod
    @tool
    def extract_info_from_query(query) -> str:
        """
            Extracts email details from a user query.

            This method analyzes the provided query to extract essential information
            needed to compose an email, including email addresses, subject, and body.
            If any required information is missing or unclear, the method indicates
            which details are lacking.

            Args:
                self: An instance of the EmailAgent class
                query (str): The user query containing information related to the email
                             to be composed.

            Returns:
                str: A formatted response that includes extracted email addresses, subject,
                     body, and any missing details, all presented in a readable format.
            """
        model = ChatOllama(model=Config.LOCAL_LLM)
        prompt = PromptTemplate(
            input_variables=["query"],
            template=(
                "You are a personal assistant. Analyze the following query and extract the necessary information to compose an email:\n\n"
                "Query: {query}\n\n"
                "Please extract the following details:\n"
                "1. Email Address(es):\n"
                "2. Subject:\n"
                "3. Body:\n\n"
                "If any of these pieces of information are missing or unclear, indicate which ones are missing."
            ),
        )

        # Generate a response from the model
        response = model.invoke(prompt.format(query=query))
        print(response)
        return response.content

    @staticmethod
    @tool
    def send_email(contact_emails, subject, email_body) -> str:
        """
        Sends an email using the Gmail API.

        This function composes an email using the specified recipient emails, subject, and body content,
        then sends it via the Gmail API. If successful, it returns a confirmation message;
        otherwise, it catches and returns any error encountered during the process.

        :param contact_emails: List of recipient email addresses to whom the email will be sent.
        :type contact_emails: list of str
        :param subject: Subject line of the email.
        :type subject: str
        :param email_body: The main content of the email to be sent.
        :type email_body: str
        :return: A message indicating whether the email was sent successfully or an error message if the email could not be sent.
        :rtype: str
        """
        credentials = GoogleAuth().authenticate()
        gmail_service = build("gmail", "v1", credentials=credentials)

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
                gmail_service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            print(f'Message Id: {send_message["id"]}')
            return "Email sent successfully!"
        except HttpError as error:
            return f"An error occurred: {error}"
