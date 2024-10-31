from googleapiclient.errors import HttpError

from main.util.google_auth import GoogleAuth
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from googleapiclient.discovery import build


class SchedulingAgent:

    def __init__(self, model):
        self.credentials = GoogleAuth().authenticate()
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
        self.scheduler_prompt = """
                You are part of a multi-agent system designed to be a personal assistant for the user. 
                Specifically, you are the **Scheduling Agent** responsible for scheduling and creating meetings on behalf of the user.
                        """
        self.scheduling_agent = create_react_agent(model, tools=[self.create_event], state_modifier=self.scheduler_prompt)

    @tool
    def create_event(self, event_payload):
        """
            Creates a calendar event using the Google Calendar API.

            This function uses the Google Calendar API to insert a new event into the primary calendar
            based on the details provided in `event_payload`. It returns the event details if the event
            is created successfully or prints an error message if there is a failure.

            :param event_payload: A dictionary containing event details, such as start and end times,
                                  summary (title), description, location, and attendees. The structure
                                  should follow the Google Calendar API's expected event format.
            :type event_payload: dict
            :return: A dictionary with details of the created event, including the event ID, start and
                     end times, and other relevant information, if successful. If there is an error,
                     returns None after printing an error message.
            :rtype: dict or None
        """
        try:
            event_result = self.calendar_service.events().insert(calendarId='primary', body=event_payload).execute()
            return event_result
        except HttpError as error:
            print(f"An error occurred: {error}")

    def get_date_events(self, date) -> str:
        """
            Retrieves all events for a specified date from the primary Google Calendar.

            Args:
                date (str): Date for which to retrieve events in 'YYYY-MM-DD' format.

            Returns:
                str: A formatted string listing all events for the specified date,
                     each on a new line in the format "start_time - summary".
                     If no events are found, returns a message stating no events were found.

            Example:
                >>> get_date_events("2024-11-01")
                "2024-11-01T10:00:00Z - Event 1\n2024-11-01T15:00:00Z - Event 2"

            Notes:
                - `timeMin` and `timeMax` are set to cover the full day based on the provided date.
                - Assumes 'calendar_service' is an authenticated Google Calendar API service instance.
                - The events are ordered by their start time.
        """
        time_min = f"{date}T00:00:00Z"  # start of the day in ISO format
        time_max = f"{date}T23:59:59Z"  # end of the day in ISO format

        # List events on a particular date
        events_result = self.calendar_service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        all_events = ""
        # Return event details
        if not events:
            return f'No events found on {date}.'
        # Iterate through each event and append its details to the string
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            all_events += f"{start} - {event['summary']}\n"
        return all_events[:-1]

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
