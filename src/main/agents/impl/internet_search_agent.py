from langchain_community.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from langchain_core.tools import tool
from tavily import TavilyClient

from main.config import Config


class InternetSearchAgent:
    def __init__(self, model):
        self.internet_search_prompt = """
                You are part of a multi-agent system designed to be a personal assistant for the user. 
                Specifically, you are the **Internet Search Agent** responsible for composing searching the internet 
                and returning a summarized response.
        """
        self.internet_search_agent = create_react_agent(model, tools=[self.search_internet],
                                                        state_modifier=self.internet_search_prompt)

    def __call__(self):
        return self.internet_search_agent

    @staticmethod
    @tool
    def search_internet(query, max_results=None):
        """
        Searches the internet for information related to the given query and summarizes the results.

        This function uses a search client to retrieve internet search results based on the input query,
        and then passes these results to an LLM model to generate a concise summary. The summary
        provides information relevant to the query, aiming to answer the query in a comprehensive yet
        succinct format.

        Args:
            query (str): The search term or question for which information is to be retrieved.
            max_results (int, optional): The maximum number of search results to retrieve. Defaults to None,
                                         which returns all available results within basic search depth.

        Returns:
            str: A summarized response generated from the search results, providing relevant information
                 related to the query.
        """
        search_client = TavilyClient(api_key=Config.SEARCH_KEY)
        content = \
            search_client.search(query, search_depth="advanced", max_results=5 if max_results is None else max_results)[
                "results"]

        prompt = [{
            "role": "system",
            "content": "You are a good internet search result summarizer\n"
                       "Your purpose is to summarize the results of internet search results "
                       "given the context of the query and return the response"
        }, {
            "role": "user",
            "content": f'Information: """{content}"""\n\n' \
                       f'Using the above information, answer the following' \
                       f'query: "{query}" ' \
            }]

        model = ChatOpenAI(model=Config.PUBLIC_LLM, api_key=Config.OPEN_AI_KEY)

        lc_messages = convert_openai_messages(prompt)
        response = model.invoke(lc_messages).content

        return response
