class Tool:
    def execute(self, details):
        """Execute the tool's primary function with the provided details.

        Parameters:
            details (str): Information the tool needs to complete its task.

        Returns:
            str: Result or outcome of the execution.
        """
        raise NotImplementedError("Each tool must implement the 'execute' method.")
