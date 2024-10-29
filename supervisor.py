from typing import List, Dict, Optional, Type

from agents.impl.email_agent import EmailAgent
from agents.impl.pdf_agent import PDFAgent
from tools.impl.email_tool import EmailTool
from tools.impl.pdf_tool import PDFTool


# Supervisor class that manages agent routing and workflow logic
# Supervisor class to manage agents

# TODO Supervisor itself is an LLM that decides where to route based on things like task, agent response
class Supervisor:
    def __init__(self):
        # Initialize agents with corresponding tools
        self.agents = {
            "email": EmailAgent(EmailTool()),
            "pdf": PDFAgent(PDFTool()),
            # "schedule": SchedulingAgent(ScheduleTool()),
            # "internet_search": InternetSearchAgent(InternetSearchTool()),
            # "question": QuestionAgent(None)  # No tool needed
        }
        self.history = []  # Track conversation history
        self.task_complete = False

    def determine_next_agent(self, task: str, current_agent: str = None) -> Optional[str]:
        # TODO better logic to which agent to route to
        # Choose agent based on task type in message
        if "email" in task:
            return "email"
        elif "pdf" in task:
            return "pdf"
        elif "schedule" in task:
            return "schedule"
        elif "search" in task:
            return "internet_search"
        elif "question" in task:
            return "question"  # Route to question agent if task is unclear
        else:
            return "FINISH"

    def process_task(self, task: str):
        self.task_complete = False
        agent_name = self.determine_next_agent(task)

        while not self.task_complete:
            agent = self.agents[agent_name]
            response = agent.handle_task(task)
            print(f"{agent_name.capitalize()} Agent Response: {response}")

            self.history.append((agent_name, response))

            agent_name = self.determine_next_agent(task)
            # Decide next step based on response
            if agent_name == "FINISH":
                self.task_complete = True  # Finish if no more agents needed
                print("Task complete.")



