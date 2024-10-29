from tools.impl.tool import Tool


class Agent:
    def __init__(self, tool: Tool):
        self.tool = tool

    def handle_task(self, state):
        """Execute the agent's task with the tool.

        Parameters:
            state (dict): The current state, containing task details.

        Returns:
            dict: Updated state with the result of the tool's execution.
        """
        raise NotImplementedError("Each agent must implement the 'handle_task' method.")
