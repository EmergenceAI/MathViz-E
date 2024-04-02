import json
import logging

from src.prompts import DESMOS_REFINEMENT_PROMPT
from src.prompts import DESMOS_REFINEMENT_PROMPT_STEP_2
from src.prompts import DESMOS_START_PROMPT
from src.prompts import DESMOS_SYSTEM_PROMPT
from src.utils import get_gpt_response

RELEVANT_EXPRESSION_KEYS = ["id", "type", "latex", "hidden", "sliderBounds"]

def encode_calculator_state_as_str(calculator_state_expressions):
    """Encode calculator state expressions as a string.

    Args:
        calculator_state_expressions (List[str]): Desmos expressions
        representing current calculator state

    Returns:
        str: Encoded calculator state
    """
    output_str = ""
    for expression in calculator_state_expressions:
        json_expr = json.loads(expression)
        expr = {k:json_expr[k] for k in json_expr.keys() if k in RELEVANT_EXPRESSION_KEYS}
        expr_str = json.dumps(expr)
        output_str += expr_str + "\n"
    return output_str

class DesmosAgent:
    """Agent responsible for generating Desmos expressions"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_desmos_expressions(
            self,
            user_request,
            calculator_state_expressions,
            wolfram_solution
    ):
        """Generate new Desmos expressions given user request and current calculator state.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state
            wolfram_solution (str): Wolfram solver solution

        Returns:
            List[dict]: Desmos expression JSON objects representing updated calculator state
            str: LLM CoT response
        """
        self.logger.info(f"Processing user request: {user_request}")
        llm_prompt = self._create_desmos_prompt(
            user_request,
            calculator_state_expressions,
            wolfram_solution
        )
        self.logger.info(f"Desmos LLM prompt:\n {llm_prompt}")
        llm_response = get_gpt_response(llm_prompt)
        self.logger.info(f"Desmos LLM response:\n {llm_response}")
        expressions = self._parse_llm_response(
            llm_response, prefix="Desmos expressions: "
        )
        return expressions, llm_response

    def validate_desmos_expressions(self, expressions):
        """Validate Desmos expressions via LLM.

        Args:
            expressions (List[dict]): Desmos expressions

        Returns:
            List[dict]: Desmos expressions
        """
        self.logger.info("Desmos refinement step 1:\n")
        refine_expressions, preserve_expressions = \
            self._extract_expressions_for_refinement(
                expressions
            )
        new_expressions = self._refine_expressions(
            refine_expressions,
            DESMOS_REFINEMENT_PROMPT
        )
        self.logger.info("Desmos refinement step 2:\n")
        new_expressions = self._refine_expressions(
            new_expressions,
            DESMOS_REFINEMENT_PROMPT_STEP_2
        )
        self.logger.info(
            f"Desmos refinement done. Expressions:\n\
                {new_expressions+preserve_expressions}"
        )
        return new_expressions + preserve_expressions

    def process_desmos_expressions(self, expressions):
        """Post process Desmos expressions via rules.
        Quicker but less robust than LLM validation.

        Args:
            expressions (List[dict]): Desmos expressions

        Returns:
            List[dict]: Desmos expressions
        """
        self.logger.info("Desmos post processing step 1:\n")
        new_expressions = [self._process_expression(expr) for expr in expressions]
        return new_expressions

    def _create_desmos_prompt(
            self,
            user_request,
            calculator_state_expressions,
            wolfram_solution
    ):
        """Create prompt for LLM to generate Desmos expressions from user request, calculator state and wolfram solution.

        Args:
            user_request (str): User request
            calculator_state_expressions (List[str]): Desmos expressions
            representing current calculator state
            wolfram_solution (str): Wolfram solver solution

        Returns:
            List[dict]: LLM prompt
        """
        messages = []
        messages.append({"role": "system", "content": DESMOS_SYSTEM_PROMPT})
        messages.append({"role": "user", "content": DESMOS_START_PROMPT})
        user_msg = f"Task: {user_request}\nCalculator state: ["
        user_msg += encode_calculator_state_as_str(calculator_state_expressions)
        user_msg += "]\nStep-by-step Solution: \n"
        user_msg += wolfram_solution + "\n"
        messages.append({"role": "user", "content": user_msg})
        return messages

    def _parse_llm_response(self, llm_response, prefix):
        """Parse LLM response to extract Desmos expressions.

        Args:
            llm_response (str): LLM response

        Returns:
            List[dict]: Desmos expressions JSON objects
        """
        expressions = []
        lines = llm_response.splitlines()
        is_expression_line = False
        for _, line in enumerate(lines):
            if is_expression_line:
                try:
                    if line.strip().startswith("{"):
                        end_char = line.rfind("}")
                        expressions.append(json.loads(line[:end_char+1]))
                    else:
                        continue
                except Exception as e:
                    self.logger.warn(f"Exception in parsing {line} in llm response: {e}")
                    continue
            if line.startswith(prefix):
                is_expression_line = True
        self.logger.info(f"Parsed updated expressions: {expressions}")
        return expressions

    def _create_refinement_prompt(self, expressions, sys_prompt):
        """Create prompt for LLM to refine Desmos expressions.

        Args:
            expressions (List[dict]): Desmos expressions

        Returns:
            List[dict]: LLM prompt
        """
        messages = []
        messages.append({"role": "system", "content": sys_prompt})
        expr = [e["expression"] for e in expressions]
        expr_str = "[\n"
        for e in expr:
            expr_str += json.dumps(e) + ",\n"
        expr_str += "]"
        messages.append({"role": "user", "content": expr_str})
        return messages

    def _refine_expressions(self, expressions, sys_prompt):
        """Refine Desmos expressions via LLM.

        Args:
            expressions (List[dict]): Desmos expressions

        Returns:
            List[dict]: Refined Desmos expressions
        """
        self.logger.info(f"Refining expressions:\n {type(expressions)}, {expressions}")
        llm_prompt = self._create_refinement_prompt(expressions, sys_prompt)
        self.logger.info(f"Desmos refinement prompt:\n {llm_prompt}")
        llm_response = get_gpt_response(llm_prompt)
        self.logger.info(f"Desmos refinement response: {llm_response}")
        refined_expressions = self._parse_llm_response(
            llm_response, prefix="Fixed Desmos expressions:"
        )
        if len(refined_expressions) != len(expressions):
            self.logger.warn(
                f"Refinement #expr mismatch: {len(refined_expressions)} vs {len(expressions)}"
            )
            refined_expressions = expressions
        else:
            refined_expressions = [
                {"action": expr["action"], "expression": ref_expr} \
                    for expr, ref_expr in zip(expressions, refined_expressions, strict=True)
            ]
        self.logger.info(f"Refined expressions:\n {refined_expressions}")
        return refined_expressions

    def _extract_expressions_for_refinement(self, expressions):
        """Extract expressions for refinement.

        Args:
            expressions (List[dict]): Desmos expressions

        Returns:
            List[dict]: Expressions for refinement
            List[dict]: Expressions to preserve
        """
        refine_expressions, preserve_expressions = [], []
        for expr in expressions:
            if expr["action"] == "setExpression":
                refine_expressions.append(expr)
            else:
                preserve_expressions.append(expr)
        self.logger.info(f"Refine expressions:\n{refine_expressions}")
        self.logger.info(f"Preserve expressions:\n{preserve_expressions}")
        return refine_expressions, preserve_expressions

    def _process_expression(self, expression):
        """Post process Desmos expression via rules

        Args:
            expression (dict): Desmos expression

        Returns:
            dict: Processed Desmos expression
        """
        # Remove any occurrence of prime notation
        new_expression = expression
        if expression["action"] == "setExpression" \
            and "latex" in expression.get("expression", {}):
            old_latex = expression["expression"]["latex"]
            # replace prime notation
            new_latex = old_latex.replace("\'", "").replace("'", "")
            new_expression["expression"]["latex"] = new_latex
        return new_expression
