from tools.impl.tool import Tool


class InternetSearchTool(Tool):
    def execute(self, details):
        print("Searching the internet for:", details)
        return "Search results found."