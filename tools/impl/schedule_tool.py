from tools.impl.tool import Tool


class ScheduleTool(Tool):
    def execute(self, details):
        print("Scheduling meeting:", details)
        return "Meeting scheduled."