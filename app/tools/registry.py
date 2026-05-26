import json
from typing import Any, Callable

from app.tools.calculator import calculate
from app.tools.time_tool import get_current_time
from app.tools.weather import get_weather

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "用于执行基础数学计算，比如加减乘除、括号运算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如：123 * 99 或 (88 + 12) / 5"
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前系统时间。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海、广州、深圳"
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }
        }
    }
]

_TOOL_FUNCTIONS: dict[str, Callable[..., str]] = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "calculator": calculate,
}

def execute_tool(tool_name: str,arguments: str)-> str:
    tool_func = _TOOL_FUNCTIONS[tool_name]
    if tool_func is None:
        return f"未知工具：{tool_name}"

    try:
        parsed_arguments: dict[str, Any] = json.loads(arguments or '{}')
        return tool_func(**parsed_arguments)
    except json.JSONDecodeError:

        return "工具参数解析失败：不是合法 JSON"

    except TypeError as exc:

        return f"工具参数错误：{exc}"

    except Exception as exc:

        return f"工具执行失败：{exc}"