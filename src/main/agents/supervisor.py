import functools
import operator
from typing import Literal, Annotated, TypedDict, Sequence

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from main.agents.impl.email_agent import EmailAgent
from main.agents.impl.question_agent import QuestionAgent
from main.agents.impl.scheduling_agent import SchedulingAgent
from main.config import Config
from pydantic import BaseModel


class RouteResponse(BaseModel):
    next: Literal["FINISH", "EmailAgent", "SchedulerAgent", "UserInputAgent"]


# Supervisor class that manages agent routing and workflow logic
# Supervisor class to manage agents
class Supervisor:

    def __init__(self, send_response_callback, wait_for_response, send_task_completed, send_task_failed):
        # members = ["EmailAgent", "PDFQueryAgent", "SchedulerAgent", "SearchAgent", "ClarificationAgent"]
        self.members = ["EmailAgent", "SchedulerAgent", "UserInputAgent"]
        self.options = ["FINISH"] + self.members
        self.model = ChatOpenAI(model="gpt-4o-mini", api_key=Config.OPEN_AI_KEY)
        self.send_response_callback = send_response_callback
        self.wait_for_response = wait_for_response
        self.send_task_completed = send_task_completed
        self.send_task_failed = send_task_failed
        self.last_task = None

    def create_supervisor_agent(self):
        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the"
            " following agents: {members}. Given the current user request, respond"
            " with the agent that should act next. When the task is complete, respond"
            " with FINISH."
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    "Given the conversation above, who should act next?"
                    " Select one of: {options}",
                ),
            ]
        ).partial(options=str(self.options), members=", ".join(self.members))
        self.supervisor_llm = ChatOpenAI(model="gpt-4o-mini", api_key=Config.OPEN_AI_KEY)
        self.supervisor_chain = prompt | self.supervisor_llm.with_structured_output(RouteResponse)

    def supervisor_agent(self, state):
        response = self.supervisor_chain.invoke(state)
        return response

    # Define agents' task execution logic
    def agent_node(self, state, agent, name, task_id):
        result = agent.invoke(state)
        self.last_task = task_id
        self.send_response_callback(task_id=task_id,
                                    message=result["messages"][-1].content)
        return {
            "messages": [HumanMessage(content=result["messages"][-1].content, name=name)]
        }

    def user_node(self, state, agent, name):
        # if not self.last_task:
        #     result = agent.invoke(state)
        #     self.last_task = 'user_input'
        #     self.send_response_callback(task_id='user_input',
        #                                 message=result['messages'][-1].content)
        #     return {
        #         "messages": [HumanMessage(content=result["messages"][-1].content, name=name)]
        #     }
        user_response = self.wait_for_response(task_id=self.last_task)
        state['messages'].append(HumanMessage(content=user_response, name=name))
        return {
            "messages": [HumanMessage(content=user_response, name=name)]
        }

    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], operator.add]
        next: str

    def create_agents(self):
        pass

    def process_task(self, task: str):
        self.create_supervisor_agent()

        # Partial function application for each agent node
        email_node = functools.partial(self.agent_node, agent=EmailAgent(model=self.model)(), name="EmailAgent",
                                       task_id="email")
        scheduling_node = functools.partial(self.agent_node, agent=SchedulingAgent(model=self.model)(),
                                            name="SchedulerAgent")
        user_input_node = functools.partial(self.user_node, agent=QuestionAgent(model=self.model)(), name="UserInput")

        workflow = StateGraph(self.AgentState)
        workflow.add_node("EmailAgent", email_node)
        workflow.add_node("SchedulerAgent", scheduling_node)
        workflow.add_node("UserInputAgent", user_input_node)
        workflow.add_node("supervisor", self.supervisor_agent)

        # Add edges to return to supervisor after each task
        for member in self.members:
            workflow.add_edge(member, "supervisor")

        # Conditional routing logic in the supervisor based on task results
        conditional_map = {k: k for k in self.members}
        conditional_map["FINISH"] = END
        workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
        workflow.add_edge(START, "supervisor")

        graph = workflow.compile()

        try:
            for s in graph.stream(
                    {
                        "messages": [
                            HumanMessage(content=task)
                        ]
                    }
            ):
                if "__end__" not in s:
                    print(s)
                    print("----")
        except Exception as e:
            print("Error:", e)
            self.send_task_failed()
        self.send_task_completed()
