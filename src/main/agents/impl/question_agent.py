from langchain_core.messages import HumanMessage

from src.main.agents.agent import Agent


class QuestionAgent(Agent):
    def handle_task(self, task):
        question = "Could you provide more details about this task?"
        return {"messages": [HumanMessage(content=question, name="Question Agent")]}
