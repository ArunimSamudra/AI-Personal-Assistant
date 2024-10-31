from langchain_core.tools import tool


class ScheduleTool:

    @tool()
    def schedule_meeting(self, date: str, time: str, participants: list):
        """Schedules a meeting on the user's calendar"""
        pass

    def check_availability(self, date: str, time: str, participants: list):
        """Checks availability """
        pass
