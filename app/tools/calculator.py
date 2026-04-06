from asteval import Interpreter

aeval = Interpreter()

def calculate(expression: str) -> dict:
    result = aeval(expression)
    if aeval.error:
        # TODO: Handle the error properly
        return {"error": str(aeval.error[0].get_error())}
    return {"result": result, "expression": expression}
