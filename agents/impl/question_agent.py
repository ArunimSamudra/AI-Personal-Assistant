from langchain_core.messages import HumanMessage

from agents.agent import Agent


class QuestionAgent(Agent):
    def handle_task(self, state):
        question = "Could you provide more details about this task?"
        return {"messages": [HumanMessage(content=question, name="Question Agent")]}
