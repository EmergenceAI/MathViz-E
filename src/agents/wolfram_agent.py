import logging
import os
import urllib.parse

import requests

from src.agents.desmos_agent import encode_calculator_state_as_str
from src.prompts import WA_QUERY_PROMPT
from src.utils import get_gpt_response


class WolframAgent:
    """Agent responsible for generating Wolfram solver queries and parsing Wolfram solver output"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.appid = os.getenv("WOLFRAM_APP_ID")

    def create_query(self, user_request, calculator_state_expressions):
        """Create Wolfram solver query based on user request and calculator state.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state

        Returns:
            str: Wolfram solver query
        """
        self.logger.info(f"Creating solver query: {user_request}")
        llm_prompt = self._create_solution_prompt(
            user_request,
            calculator_state_expressions
        )
        self.logger.info(f"LLM prompt: {llm_prompt}")
        response = get_gpt_response(llm_prompt)
        self.logger.info(f"LLM response: {response}")
        return response

    def execute_query(self, solver_query):
        """Execute Wolfram solver query and return the solution.

        Args:
            solver_query (str): Wolfram solver query

        Returns:
            str: Wolfram solver solution
        """
        self.logger.info(f"Executing solver query: {solver_query}")
        parsed_query = urllib.parse.quote_plus(solver_query)
        query_url = f"http://api.wolframalpha.com/v2/query?" \
                f"appid={self.appid}" \
                f"&input={parsed_query}" \
                f"&format=plaintext" \
                f"&podstate=Step-by-step%20solution" \
                f"&output=json"
        r = requests.get(query_url).json()
        #logic behind pod selection: It would be great to ask specifically for the Result pod in the query itself
        #to reduce the amount of data returned, but there is no guarantee that the necessary pod will be titled "Result"
        #the most relevant pod is almost always the second one, so we only return data from the second pod
        #this could break if Wolfram Alpha changes how they rank their pods
        numpods = r["queryresult"]["numpods"]
        if numpods < 2:
            result = "Cannot return solution"
        else:
            pod = r["queryresult"]["pods"][1]
            numsubpods = pod["numsubpods"]
            result = ""
            for subpod in range(numsubpods):
                result += pod["subpods"][subpod]["plaintext"]
                result += "\n"
        self.logger.info(f"Solver solution: {result}")
        return result

    def _create_solution_prompt(self, user_request, calculator_state_expressions):
        """Create prompt for LLM to generate Wolfram solver query from user request and calculator state.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state

        Returns:
            str: LLM prompt
        """
        messages = [{"role": "system", "content": WA_QUERY_PROMPT}]
        user_msg = f"Task: {user_request}\nCalculator state: ["
        user_msg += encode_calculator_state_as_str(calculator_state_expressions)
        messages.append({"role": "user", "content": user_msg})
        return messages
