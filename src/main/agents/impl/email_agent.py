# # import ollama
import random

from flask_socketio import SocketIO

from main.tools.impl.google_tool import GoogleTool
from src.main.agents.agent import Agent

from src.main.tools.tool import Tool


class EmailAgent(Agent):

    def __init__(self, tool: Tool, socketio: SocketIO, send_response_callback, wait_for_response):
        super().__init__(tool, socketio, send_response_callback, wait_for_response)
        self.tool = GoogleTool()

    def handle_task(self, task):
        emails, names = [], []

        while len(emails) == 0:
            emails, names = self.find_contact(task)
            if len(emails) != 0:
                break
            self.send_response_callback(task_id='email_input', message="Could not find names of recipients, please enter them")
            task = self.wait_for_response(task_id='email_input')

        print(f"Found contacts: {emails}")

        self.send_response_callback(task_id='brief_content_task', message="Please provide a brief content for the email:")
        brief_content = self.wait_for_response(task_id='brief_content_task')
        email_body = self.generate_email_content(brief_content, emails)
        approved = False
        while not approved:
            print("\nGenerated Email Body:\n", email_body)
            confirm_body = self.send_response_callback(task_id='brief_content_task', message="Do you want to approve this email body? (yes/no) ")
            if confirm_body.lower() not in ['y', 'yes']:
                email_body = self.generate_email_content(brief_content, names)
            else:
                approved = True

        # Generate email subject
        # subject_prompt = f"Suggest a subject line for the following email: {email_body}"
        # # TODO
        # subject = ollama.call("your_model_name", subject_prompt)  # Replace with your Ollama model
        # subject_approval = False
        # while not subject_approval:
        #     print("Suggested Subject:", subject)
        #
        #     confirm_subject = input("Do you want to approve this subject? (yes/no) ")
        #     if confirm_subject.lower() != 'yes':
        #         subject_prompt = f"Suggest a subject line for the following email: {email_body}"
        #         subject = ollama.call("your_model_name", subject_prompt)  # Replace with your Ollama model
        #     else:
        #         subject_approval = True
        #
        # # Send email (replace with your actual email sending logic)
        # print(f"Sending email to {emails}...")
        # self.tool.send_email(emails, subject, email_body)  # Uncomment and implement this function
        # print("Email sent successfully!")
        return "successful"

    # Fetch email contact based on user query
    def find_contact(self, query):
        while True:
            recipient_names = self.find_recipient_names(query)

            email = []
            if recipient_names:
                for name in recipient_names:
                    # TODO handle multiple names
                    email = self.tool.find_email_by_name(name)
                    if email:
                        print(f"Found email for {name}: {email}")
                        email.append(email)
            else:
                print("No suitable recipient found. Please provide more details.")
            return email, recipient_names

    def find_recipient_names(self, query: str):
        # prompt = f"Based on the user query '{query}', suggest the names of the email recipients. If no suitable names can be found, request more details."
        # response = ollama.call("your_model_name", prompt)  # Replace with your Ollama model
        # return response.get('names', [])
        if random.random() > 0.9:
            return ["arunim"]
        return []

    # Generate email body and subject using the LLM
    def generate_email_content(self, content, contacts):
        # prompt = f"Write an email to {contacts} with the following content: {content}"
        # response = ollama.call("your_model_name", prompt)  # Replace with your Ollama model
        # return response
        return "Email body"
