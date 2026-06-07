import re
from typing import Literal, TypedDict
from langgraph.graph import START, END, StateGraph
from app.tools.calculator import calculate

class BasicWorkflowState(TypedDict):
    """
    LangGraph 共享状态。

    user_input: 用户输入
    route: 路由结果
    answer: 最终回答
    """
    user_input: str
    route: str
    answer: str

def classify_input(
        state: BasicWorkflowState,
) -> BasicWorkflowState:
    """
    判断用户输入应该走哪个节点。

    这里先用规则分类：
    - 包含数学表达式特征 → calculator
    - 其他 → answer
    """
    user_input = state["user_input"]
    if _is_math_math_expression(user_input):
        route = 'calculator'
    else:
        route = 'answer'
    return {
        **state,
        'route': route,
    }

def answer_node(
        state: BasicWorkflowState,
) -> BasicWorkflowState:
    """
    普通回答节点。

    第一天先不用 LLM，先专注理解 LangGraph 流程。
    """
    user_input = state["user_input"]
    return {
        **state,
        'answer': f"这是普通问题，我收到你的输入：{user_input}",
    }

def calculator_node(
        state: BasicWorkflowState,
) -> BasicWorkflowState:
    user_input = state["user_input"]
    expression = _extract_math_expression(user_input)
    answer = calculate(expression)
    return {
        **state,
        'answer': answer,
    }

def route_after_classification(
        state: BasicWorkflowState,
) -> Literal['calculator', 'answer']:
    """
    Conditional Edge 路由函数。

    返回值必须能映射到下一个节点名。
    """
    route = state["route"]
    if route == 'calculator':
        return 'calculator'
    else:
        return 'answer'

def build_basic_workflow():
    graph = StateGraph(BasicWorkflowState)
    graph.add_node('classify_input', classify_input)
    graph.add_node('answer', answer_node)
    graph.add_node('calculator', calculator_node)

    graph.add_edge(START, 'classify_input')
    graph.add_conditional_edges('classify_input', route_after_classification,
                                {'calculator': 'calculator', 'answer': 'answer'})
    graph.add_edge('answer', END)
    graph.add_edge('calculator', END)
    return graph.compile()


def _is_math_math_expression(expr: str) -> bool:
    """
    简单判断文本中是否像数学计算问题。
    """
    return bool(
        re.search(r"\d+\s*[\+\-\*/%]\s*\d+", expr)
        or any(keyword in expr for keyword in ["计算", "等于多少", "加", "减", "乘", "除"])
    )


def _extract_math_expression(expr: str) -> str:
    """
    从用户输入中提取数学表达式。

    示例：
    - "123 * 99 等于多少" -> "123 * 99"
    - "请计算 (88 + 12) / 5" -> "(88 + 12) / 5"
    """
    match = re.search(r"[\d\.\+\-\*/%\(\)\s]+", expr)
    if not match:
        return expr

    return match.group(0).strip()