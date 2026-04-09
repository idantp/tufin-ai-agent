"""
Calculator tool for safely evaluating mathematical expressions.

Uses asteval.Interpreter as a sandboxed evaluator — no imports, no builtins,
no arbitrary code execution. Only mathematical expressions are permitted.
"""

import logging

from asteval import Interpreter
from app.tools.models import CalculatorOutput
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression to evaluate (e.g. "1 + 1", "2 * 3", "sqrt(4)").

    Returns JSON string with:
        - "result": the numeric result of the expression
        - "error": the error message if the evaluation failed
    """
    logger.debug("Evaluating expression: %s", expression)

    aeval = Interpreter(no_print=True)
    result = aeval(expression)

    if aeval.error:
        error_msg = "; ".join(str(err.get_error()[1]) for err in aeval.error)
        logger.warning("Expression evaluation failed: %s | error: %s", expression, error_msg)
        return CalculatorOutput(error=error_msg).model_dump_json()
    elif not isinstance(result, int | float):
        error_msg = f"Expression did not produce a numeric result, got {type(result).__name__}"
        logger.warning("Non-numeric result: %s | type: %s", expression, type(result).__name__)
        return CalculatorOutput(error=error_msg).model_dump_json()

    logger.debug("Expression result: %s = %s", expression, result)
    return CalculatorOutput(result=result).model_dump_json()
