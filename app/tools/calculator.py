"""
Calculator tool for safely evaluating mathematical expressions.

Uses asteval.Interpreter as a sandboxed evaluator — no imports, no builtins,
no arbitrary code execution. Only mathematical expressions are permitted.
"""

import logging

from asteval import Interpreter
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class CalculatorInput(BaseModel):
    """Input model for the calculator tool."""

    expression: str = Field(
        min_length=1,
        max_length=500,
        description="A mathematical expression to evaluate (e.g. '2 + 2 * 3')",
    )


class CalculatorOutput(BaseModel):
    """Output model for the calculator tool."""

    result: float | int | None = Field(
        default=None,
        description="The numeric result of the expression, or None if evaluation failed",
    )
    error: str | None = Field(
        default=None,
        description="Error message if evaluation failed, otherwise None",
    )


def calculate(input: CalculatorInput) -> CalculatorOutput:
    """
    Safely evaluate a mathematical expression.

    Uses asteval.Interpreter which restricts execution to math-safe operations:
    no imports, no attribute access to builtins, no arbitrary code execution.

    Args:
        input: CalculatorInput containing the expression to evaluate.

    Returns:
        CalculatorOutput with a numeric result, or an error message on failure.
    """
    logger.debug("Evaluating expression: %s", input.expression)

    aeval = Interpreter(no_print=True)
    result = aeval(input.expression)

    if aeval.error:
        error_msg = "; ".join(str(err.get_error()[1]) for err in aeval.error)
        logger.warning("Expression evaluation failed: %s | error: %s", input.expression, error_msg)
        return CalculatorOutput(error=error_msg)

    if not isinstance(result, int | float):
        error_msg = f"Expression did not produce a numeric result, got {type(result).__name__}"
        logger.warning("Non-numeric result: %s | type: %s", input.expression, type(result).__name__)
        return CalculatorOutput(error=error_msg)

    logger.debug("Expression result: %s = %s", input.expression, result)
    return CalculatorOutput(result=result)
