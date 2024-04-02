import json
import logging

from src.agents.desmos_agent import DesmosAgent
from src.agents.desmos_agent import encode_calculator_state_as_str
from src.agents.wolfram_agent import WolframAgent
from src.prompts import EXPLANATION_PROMPT
from src.utils import get_gpt_response


class MathVizAgent:
    """Math visualization gent responsible for orchestrating Wolfram and Desmos agents to handle user request."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.wolfram_agent = WolframAgent()
        self.desmos_agent = DesmosAgent()

    def _return_agent_response(self, agent:str, status_message:str):
        """Return agent status message in JSON format to front-end

        Args:
            agent (str): Agent name
            status_message (str): Status message

        Returns:
            str: JSON formatted agent status message
        """
        json_status_message = {"agent": agent, "message": status_message}
        self.logger.info(f"Returning agent response: {json_status_message}")
        return json.dumps(json_status_message) + "\n"


    def process_user_request(
        self,
        user_request,
        calculator_state_expressions,
        use_validation=False
    ):
        """Process user request, given the current calculator state,
        and return the updated calculator state.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state
            use_validation (bool, optional): Whether to validate Desmos expressions. Defaults to False.

        Returns:
            List[str]: Desmos expressions representing Updated calculator state
        """

        self.logger.info(f"Processing user request: {user_request}")
        self.logger.info(f"Calculator state: {calculator_state_expressions}")

        wolfram_query = self.wolfram_agent.create_query(
            user_request,
            calculator_state_expressions
        )
        yield self._return_agent_response("wolfram", f"Reformulated user request for Wolfram|Alpha solver: {wolfram_query}")

        wolfram_solution = self.wolfram_agent.execute_query(
            wolfram_query
        )
        if wolfram_solution.strip() != "Cannot return solution" and len(wolfram_solution.strip()) > 0:
            yield self._return_agent_response("wolfram", f"Wolfram solution: {wolfram_solution}")

        yield self._return_agent_response("math viz", "Generating Desmos expressions for user query ...")
        new_calculator_expressions, chain_of_thought = self.desmos_agent.generate_desmos_expressions(
            user_request,
            calculator_state_expressions,
            wolfram_solution
        )
        yield self._return_agent_response("math viz", f"{chain_of_thought}")

        if use_validation:
            yield self._return_agent_response("math viz", "Validating expressions ...")
            new_calculator_expressions = self.desmos_agent.validate_desmos_expressions(
                new_calculator_expressions
            )
        else:
            yield self._return_agent_response("math viz", "Post-processing expressions ...")
            new_calculator_expressions = self.desmos_agent.process_desmos_expressions(
                new_calculator_expressions
            )

        yield self._return_agent_response("math viz", "Done. Visualising results on calculator.")
        expressions={"expressions": new_calculator_expressions}
        yield json.dumps(expressions)+"\n"

    def _create_explanation(self, user_request, calculator_state_expressions, solution):
        """Create an explanation of the solution based on the user request and calculator state.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state
            solution (str): Wolfram solver solution

        Returns:
            str: Explanation of the solution
        """
        self.logger.info(f"Creating explanation: {user_request}")
        llm_prompt = self._create_explanation_prompt(
            user_request,
            calculator_state_expressions,
            solution
        )
        self.logger.info(f"LLM prompt: {llm_prompt}")
        gpt_response = get_gpt_response(llm_prompt)
        self.logger.info(f"LLM explanation: {gpt_response}")
        return gpt_response

    def _create_explanation_prompt(
            self,
            user_request,
            calculator_state_expressions,
            wolfram_solution=None
        ):
        """Create prompt for LLM to generate Wolfram solver query from user request and calculator state.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state
            wolfram_solution (str, optional): Wolfram solver solution. Defaults to None.

        Returns:
            List[dict]: LLM prompt
        """
        messages = [{"role": "system", "content": EXPLANATION_PROMPT}]
        user_msg = f"Task: {user_request}\nCalculator state: ["
        user_msg += encode_calculator_state_as_str(calculator_state_expressions)
        user_msg += "]\nStep-by-step Solution: \n"
        user_msg += wolfram_solution + " \n"
        messages.append({"role": "user", "content": user_msg})
        return messages
