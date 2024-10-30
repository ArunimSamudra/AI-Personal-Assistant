from flask_socketio import SocketIO

from main.tools.impl.google_tool import GoogleTool
from src.main.agents.agent import Agent
from src.main.tools.tool import Tool


class SchedulingAgent(Agent):

    def __init__(self, tool: Tool, socketio: SocketIO):
        super().__init__(tool, socketio, None, None)
        self.tool = GoogleTool()
        self.meeting_info = {"summary": None, "start": None, "end": None, "attendees": None, "location": None,
                             "description": None}

    def handle_task(self, task):
        # Main workflow for scheduling a meeting
        self.parse_user_input(task)

        # Check for missing required information and prompt the user if needed
        missing_info = self.check_missing_info()
        while missing_info:
            self.prompt_for_missing_info(missing_info)
            missing_info = self.check_missing_info()

        # Create the event payload and schedule the meeting
        event_payload = self.generate_meeting_payload()
        event_result = self.tool.create_event(event_payload)
        print("Meeting scheduled successfully:", event_result.get('htmlLink'))

    def parse_user_input(self, user_input):
        # Step 1: LLM parses user input to try to extract date_time, agenda, and recipients
        prompt = (
            f"Extract summary, start time, end time, attendees, location, and description from this statement: '{user_input}'. "
            "If any information is missing, respond with 'missing' for that field."
        )
        response = self.ollama.chat(prompt)
        parsed_info = response['message']

        # Assume response is a dictionary with keys: date_time, agenda, and recipients
        self.meeting_info.update(parsed_info)

    def check_missing_info(self):
        # Returns a list of missing information fields
        missing_info = [key for key, value in self.meeting_info.items() if value is None]
        return missing_info

    def prompt_for_missing_info(self, missing_info):
        # Prompt user for each piece of missing required information
        prompts = {
            "summary": "Please provide a summary or title for the meeting.",
            "start": "Please specify a start date and time for the meeting",
            "end": "Please specify an end date and time for the meeting",
            "attendees": "Who should be invited to this meeting? Please provide their email address"
        }
        for field in missing_info:
            self.meeting_info[field] = input(prompts[field])

    def generate_meeting_payload(self):
        # Define example payload to guide the LLM
        example_payload = {
            'summary': 'Team Sync Meeting',
            'location': 'Location',
            'description': 'Weekly sync to discuss project updates and next steps.',
            'start': {
                'dateTime': '2024-11-01T14:00:00-07:00',
                'timeZone': 'America/Los_Angeles'
            },
            'end': {
                'dateTime': '2024-11-01T15:00:00-07:00',
                'timeZone': 'America/Los_Angeles'
            },
            'attendees': [
                {'email': 'teammember1@example.com'},
                {'email': 'teammember2@example.com'}
            ]
        }

        # LLM prompt for generating payload
        prompt = (
            f"Create a meeting payload for the Google Calendar API from this input:\n\n"
            f"Input: '{self.meeting_info}'\n\n"
            f"Here is an example payload:\n\n{example_payload}\n\n"
            f"Ensure that date and time values are in ISO 8601 format. "
            f"Fill in all required fields: summary, start, end, attendees. "
            f"Add location and description if provided. Convert natural date expressions to ISO format."
        )

        # Send prompt to LLM
        response = ollama.chat(prompt)
        # Parse the LLM response to extract JSON-like payload
        event_payload = response['message']  # Expected to be a dictionary formatted payload

        return event_payload
