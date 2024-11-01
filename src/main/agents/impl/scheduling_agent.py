from googleapiclient.errors import HttpError
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from main.config import Config
from main.util.google_auth import GoogleAuth
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from googleapiclient.discovery import build


class SchedulingAgent:

    def __init__(self, model):
        self.scheduler_prompt = """
                You are part of a multi-agent system designed to be a personal assistant for the user. 
                Specifically, you are the **Scheduling Agent** responsible for organizing, scheduling, and 
                creating meetings on behalf of the user. 
                
                Your goal is to create meetings efficiently and accurately, confirming details with the user if there are any uncertainties.

                To successfully schedule a meeting, you need the following required information:
                1. **Meeting Summary/Title**: A brief title or summary for the meeting.
                2. **Start Date and Time**: The date and start time for the meeting.
                3. **End Date and Time**: The date and end time for the meeting.
                
                Additionally, you may also gather the following optional details:
                - **Attendees**: Email addresses of the people to invite.
                - **Location**: A specific location for the meeting, if applicable.
                - **Meeting Description**: Additional information or details about the meeting.
                
                **Responsibilities and Guidelines**:
                
                1. **Extract Required Information**:
                   - Upon receiving a user query, identify and extract the required fields: meeting summary, 
                   start date and time, and end date and time.
                   - If any required field is missing, ask the user to provide it in a clear and concise manner.
                
                2. **Extract Optional Information**:
                   - If the user’s query includes additional details such as attendees, location, or description, 
                   include these in the meeting details.
                   - If any optional information appears unclear, politely ask the user for clarification.
                
                3. **Handle Ambiguity and Clarification**:
                   - If there is any ambiguity in the information provided (e.g., unclear date or time), 
                   ask the user for more clarification before proceeding.
                   
                4. **Check for Time Conflicts**:
                   - For the proposed start and end times, check the user’s calendar to ensure there are no scheduling conflicts.
                   - If there are no conflicts, proceed to schedule the meeting and confirm it with the user.
                   - If there is a conflict, inform the user about the conflicting appointment and provide a list of 
                   alternative times available on that day, allowing the user to choose a suitable time.
                
                5. **Confirm and Notify**:
                   - Once all details are confirmed and any conflicts are resolved, create the meeting in the calendar 
                   and inform the user that the meeting has been successfully scheduled.
                   - If there are any issues with scheduling, such as permission errors, inform the user promptly 
                   and provide guidance on how to proceed.
                
                Your objective is to ensure that meetings are scheduled accurately, with user confirmation, and that any 
                potential conflicts or uncertainties are resolved efficiently through clear communication with the user.
                        """
        self.scheduling_agent = create_react_agent(model, tools=[self.extract_info_from_query, self.get_date_events,
                                                                 self.generate_meeting_payload, self.create_event],
                                                   state_modifier=self.scheduler_prompt)

    def __call__(self, *args, **kwargs):
        return self.scheduling_agent

    @staticmethod
    @tool
    def extract_info_from_query(query) -> str:
        """
            Extracts email details from a user query.

            This method analyzes the provided query to extract essential information
            needed to schedule a meeting, including summary, start time, end time,
            description, location, and attendees. If any required information is
            missing or unclear, the method indicates which details are lacking.

            Args:
                query (str): The user query containing information related to the
                             meeting to be scheduled.

            Returns:
                str: A formatted response that includes the extracted summary, start time,
                     end time, description, location, attendees, and any missing details, all
                     presented in a readable format.
        """
        model = ChatOpenAI(model="gpt-4o-mini", api_key=Config.OPEN_AI_KEY)
        prompt = PromptTemplate(
            input_variables=["query"],
            template=(
                "Analyze the following query and extract the necessary information to schedule a meetin:\n\n"
                "Query: {query}\n\n"
                "Please extract the following details:\n"
                "1. Summary:\n"
                "2. Start time:\n"
                "3. End time:\n"
                "4. Description:\n"
                "5. Location:\n"
                "6. Attendees:\n\n"
                "Extract the date and time values in ISO 8601 format. "
                "If any of these pieces of information are missing or unclear, indicate which ones are missing."
            ),
        )

        # Generate a response from the model
        response = model.invoke(prompt.format(query=query))
        return response.content

    @staticmethod
    @tool
    def create_event(event_payload):
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
        credentials = GoogleAuth().authenticate()
        calendar_service = build('calendar', 'v3', credentials=credentials)
        try:
            event_result = calendar_service.events().insert(calendarId='primary', body=event_payload).execute()
            return "Meeting scheduled successfully:", event_result.get('htmlLink')
        except HttpError as error:
            return f"An error occurred: {error}"

    @staticmethod
    @tool
    def get_date_events(date) -> str:
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
        credentials = GoogleAuth().authenticate()
        calendar_service = build('calendar', 'v3', credentials=credentials)

        time_min = f"{date}T00:00:00Z"  # start of the day in ISO format
        time_max = f"{date}T23:59:59Z"  # end of the day in ISO format

        # List events on a particular date
        events_result = calendar_service.events().list(
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

    @staticmethod
    @tool
    def generate_meeting_payload(summary: str, start: dict, end: dict, location: str = None, description: str = None,
                                 attendees: list[dict] = None):
        """
        Generates a meeting payload for the Google Calendar API using the provided meeting details.
        Constructs a JSON-compatible dictionary with required and optional fields for scheduling a meeting,
        following the Google Calendar API format.

        :param summary: The title or summary of the meeting (required).
        :param start: A dictionary specifying the start date and time in ISO 8601 format and timezone (required).
                      Example format: {'dateTime': '2024-11-01T14:00:00-07:00', 'timeZone': 'America/Los_Angeles'}
        :param end: A dictionary specifying the end date and time in ISO 8601 format and timezone (required).
                    Example format: {'dateTime': '2024-11-01T15:00:00-07:00', 'timeZone': 'America/Los_Angeles'}
        :param location: The location for the meeting (optional).
        :param description: A brief description or agenda for the meeting (optional).
        :param attendees: A list of dictionaries representing attendees, with each dictionary containing an 'email' key.
                          Example: [{'email': 'teammember1@example.com'}, {'email': 'teammember2@example.com'}] (optional).

        :return: A dictionary representing the formatted meeting payload, ready for submission to the Google Calendar API.
        """
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

        # Send prompt to LLM
        model = ChatOpenAI(model="gpt-4o-mini", api_key=Config.OPEN_AI_KEY)

        prompt = PromptTemplate(
            input_variables=["summary", "start", "end", "location", "description", "attendees"],
            template=(
                f"Create a meeting payload for the Google Calendar API from this input:\n\n"
                f"Summary: '{summary}'\n\n"
                f"Start time: '{start}'\n\n"
                f"End time: '{end}'\n\n"
                f"Description: '{description}'\n\n"
                f"Location: '{location}'\n\n"
                f"Attendees: '{attendees}'\n\n"
                f"Here is an example payload:\n\n{example_payload}\n\n"
                f"Ensure that date and time values are in ISO 8601 format. "
                f"Fill in all required fields: summary, start, end. "
                f"Add other fields if provided. Convert natural date expressions to ISO format."
            ),
        )
        response = model.invoke(
            prompt.format(summary=summary, start=start, end=end, location=location, description=description,
                          attendees=attendees)
        )
        return response.content
