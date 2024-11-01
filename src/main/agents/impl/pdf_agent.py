from langchain_core.messages import HumanMessage


class PDFAgent:
    def handle_task(self, task):
        result = self.tool.execute(task["messages"][-1].content)
        return {"messages": [HumanMessage(content=result, name="PDF Agent")]}
