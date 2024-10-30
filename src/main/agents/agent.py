from flask_socketio import SocketIO

from src.main.tools.tool import Tool


class Agent:
    def __init__(self, tool: Tool, socketio: SocketIO):
        self.tool = tool
        self.socketio = socketio
        self.user_responses = {}

    def handle_task(self, task):
        """Execute the agent's task with the tool.

        Parameters:
            task : The task to be performed by the agent

        Returns:
            dict: Updated state with the result of the tool's execution.
        """
        raise NotImplementedError("Each agent must implement the 'handle_task' method.")

    def wait_for_response(self, task_id):
        """Wait for a response from the user for a given task ID."""
        while task_id not in self.user_responses:
            self.socketio.sleep(0.1)
        response = self.user_responses.pop(task_id)
        return response

    def send_response_callback(self, task_id, message):
        """Send a message to the client."""
        self.socketio.emit('receive_message', message)
        user_response = self.wait_for_response(task_id)  # Wait for the user's reply
        return user_response
