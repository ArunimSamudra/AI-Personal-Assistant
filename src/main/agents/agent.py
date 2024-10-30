from flask_socketio import SocketIO

from src.main.tools.tool import Tool


class Agent:
    def __init__(self, tool: Tool, socketio: SocketIO, send_response_callback, wait_for_response):
        self.tool = tool
        self.socketio = socketio
        self.send_response_callback = send_response_callback
        self.wait_for_response = wait_for_response

    def handle_task(self, task):
        """Execute the agent's task with the tool.

        Parameters:
            task : The task to be performed by the agent

        Returns:
            dict: Updated state with the result of the tool's execution.
        """
        raise NotImplementedError("Each agent must implement the 'handle_task' method.")
