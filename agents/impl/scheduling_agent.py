from langchain_core.messages import HumanMessage

from agents.agent import Agent


class SchedulingAgent(Agent):
    def handle_task(self, state):
        result = self.tool.execute(state["messages"][-1].content)
        return {"messages": [HumanMessage(content=result, name="Scheduling Agent")]}
