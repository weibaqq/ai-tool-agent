from app.llm.chat_client import chat_with_tools

SYSTEM_PROMPT = (
    "你是一个 AI Tool Agent。"
    "当用户问题需要计算、时间或天气信息时，优先调用工具。"
    "回答要简洁、准确。"
)


def chat_once(user_message: str) -> str:
    if not user_message.strip():
        raise ValueError("用户输入不能为空")

    messages = [
        {
            'role': 'system',
            'content': SYSTEM_PROMPT
        },
        {
            'role': 'user',
            'content': user_message.strip()
        }
    ]

    return chat_with_tools(messages)
