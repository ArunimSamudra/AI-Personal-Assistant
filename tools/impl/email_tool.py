from tools.impl.tool import Tool


class EmailTool(Tool):
    def execute(self, details):
        print("Sending email:", details)
        return "Email sent."