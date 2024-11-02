from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool


class QuestionAgent:

    def __init__(self, model):
        self.user_input_agent_prompt = \
            """
            You are part of a multi-agent system designed to be personal assistant.
            Specifically, you are an agent of this system every agent turns to when they want user to give
            for more information. You also are able to converse for normal greeting based questions.
            """
        self.user_input_agent = create_react_agent(model, tools=[self.ask_question], state_modifier=self.user_input_agent_prompt)

    def __call__(self, *args, **kwargs):
        return self.user_input_agent

    @staticmethod
    @tool
    def ask_question(**kwargs):
        """
        Placeholder tool for asking questions
        :param kwargs:
        :return:
        """
        return None

