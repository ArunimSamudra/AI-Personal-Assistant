import functools
import operator
from typing import Literal, Annotated, TypedDict, Sequence

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM, ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from main.agents.impl.email_agent import EmailAgent
from main.agents.impl.internet_search_agent import InternetSearchAgent
from main.agents.impl.rag_agent import RAGAgent
from main.agents.impl.question_agent import QuestionAgent
from main.agents.impl.scheduling_agent import SchedulingAgent
from main.config import Config
from pydantic import BaseModel


class RouteResponse(BaseModel):
    next: Literal["FINISH", "EmailAgent", "RAGAgent", "SchedulerAgent", "InternetSearchAgent", "UserInputAgent"]


# Supervisor class that manages agent routing and workflow logic
# Supervisor class to manage agents
class Supervisor:

    def __init__(self, send_response_callback, wait_for_response, send_task_completed, send_task_failed):
        self.members = ["EmailAgent", "RAGAgent", "SchedulerAgent", "InternetSearchAgent", "UserInputAgent"]
        self.options = ["FINISH"] + self.members
        self.public_model = ChatOpenAI(model=Config.PUBLIC_LLM, api_key=Config.OPEN_AI_KEY)
        self.private_model = ChatOllama(model=Config.LOCAL_LLM)
        self.send_response_callback = send_response_callback
        self.wait_for_response = wait_for_response
        self.send_task_completed = send_task_completed
        self.send_task_failed = send_task_failed
        self.last_task = None

    def create_supervisor_agent(self):
        system_prompt = (
            "You are a supervisor tasked with managing a conversation between the following agents:\n\n"
            "{members}\n\n"
            "Each agent has a specific function:\n"
            "- **EmailAgent**: Composes, drafts, and sends emails on behalf"
            " of the user, collecting details such as recipient, subject, and body content if missing.\n"
            "- **RAGAgent**: Retrieves and summarizes specific information from internal"
            " or predefined knowledge sources, especially when user queries relate to structured or internal content.\n"
            "- **SchedulerAgent**: Schedules and manages calendar events, gathering "
            "details such as meeting time, date, location, and attendees, and checks for availability conflicts.\n"
            "- **InternetSearchAgent**: Searches the internet to gather up-to-date external "
            "information on user queries, and summarizes search results if needed.\n"
            "- **UserInputAgent**: Interacts with the user to clarify details, gather missing "
            "information, or confirm responses when other agents require additional input.\n\n"
            "Given the user’s current request, select the most appropriate agent based on the task "
            "requirements. The selection should be based on the nature of the query:\n"
            "- **Information Retrieval**: For factual questions or requests for summaries, choose "
            "either **RAGAgent** or **InternetSearchAgent** based on whether the information is internal or external.\n"
            "- **Email Composition**: For requests related to composing or sending an email, "
            "select **EmailAgent**.\n"
            "- **Event Scheduling**: If the user is trying to create or manage a calendar event, "
            "choose **SchedulerAgent**.\n"
            "- **Additional Input Needed**: If an agent requires further clarification or information "
            "to proceed, select **UserInputAgent**.\n\n"
            "Before ending the process with FINISH, route to UserInputAgent and ask if they need any more help for"
            "their task with any other agent"
            "When all necessary tasks are complete, respond with FINISH. Base your decisions on the "
            "agent roles and task requirements described above."
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
        self.supervisor_chain = prompt | self.public_model.with_structured_output(RouteResponse)

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
        # if not self.last_task or self.last_task == 'user_input':
        #     result = agent.invoke(state)
        #     self.send_response_callback(task_id='user_input',
        #                                 message=result['messages'][-1].content)
        #     return {
        #         "messages": [HumanMessage(content=result["messages"][-1].content, name=name)]
        #     }
        user_response = self.wait_for_response(task_id=self.last_task)
        self.last_task = 'user_input'
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
        email_node = functools.partial(self.agent_node, agent=EmailAgent(model=self.public_model)(), name="EmailAgent",
                                       task_id="email")
        scheduling_node = functools.partial(self.agent_node, agent=SchedulingAgent(model=self.public_model)(),
                                            name="SchedulerAgent", task_id="scheduling")
        internet_search_node = functools.partial(self.agent_node, agent=InternetSearchAgent(model=self.public_model)(),
                                                 name="InternetSearchAgent", task_id="internet search")
        rag_node = functools.partial(self.agent_node, agent=RAGAgent(model=self.private_model)(),
                                     name="RAGAgent", task_id="rag")
        user_input_node = functools.partial(self.user_node, agent=QuestionAgent(model=self.public_model)(),
                                            name="UserInput")

        workflow = StateGraph(self.AgentState)
        workflow.add_node("EmailAgent", email_node)
        workflow.add_node("SchedulerAgent", scheduling_node)
        workflow.add_node("UserInputAgent", user_input_node)
        workflow.add_node("InternetSearchAgent", internet_search_node)
        workflow.add_node("RAGAgent", rag_node)
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
                    },
                    {"recursion_limit": 100}
            ):
                if "__end__" not in s:
                    print(s)
                    print("----")
        except Exception as e:
            print("Error:", e)
            self.send_task_failed()
        self.send_task_completed()
