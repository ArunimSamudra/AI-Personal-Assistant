from src.main.tools.tool import Tool


class PDFTool(Tool):
    def execute(self, details):
        print("Reading PDF:", details)
        return "PDF content analyzed."