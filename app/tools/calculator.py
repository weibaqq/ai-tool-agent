import ast
import operator


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression: str) -> str:
    """
    Safely evaluate a simple arithmetic expression.

    Supported:
    - +, -, *, /, //, %, **
    - parentheses
    - positive / negative numbers
    """
    try:
        node = ast.parse(expression, mode="eval")
        result = _eval_node(node.body)
        return str(result)
    except Exception as exc:
        return f"计算失败：{exc}"


def _eval_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _ALLOWED_OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        value = _eval_node(node.operand)
        return _ALLOWED_OPERATORS[type(node.op)](value)

    raise ValueError("只支持基础数学表达式")