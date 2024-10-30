from langchain_core.messages import HumanMessage

from src.main.agents.agent import Agent


class PDFAgent(Agent):
    def handle_task(self, task):
        result = self.tool.execute(task["messages"][-1].content)
        return {"messages": [HumanMessage(content=result, name="PDF Agent")]}
