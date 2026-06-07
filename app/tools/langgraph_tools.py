from langchain_core.tools import tool

from app.tools.time_tool import get_current_time
from app.tools.calculator import calculate
from app.tools.weather import get_weather

@tool
def calculator(expression: str) -> str:
    """
    用于执行数学表达式计算

    Args:
        expression (str): 数学表达式，例如 "123 * 99" 或 "(88 + 12) / 5"
    """
    return calculate(expression)

@tool
def current_time() -> str:
    """
    获取当前系统时间
    """
    return get_current_time()

@tool
def weather(city: str) -> str:
    """
    查询指定城市的天气信息。

    Args:
        city: 城市名称，例如 北京、上海、广州、深圳
    """
    return get_weather(city)

def get_agent_tools():
    return [calculator, current_time, weather]