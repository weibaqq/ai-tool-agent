from typing import Any

from llm.client import chat_with_tools

def main():
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个 AI Tool Agent。"
                "当用户的问题需要计算、时间或天气信息时，你应该优先调用工具。"
                "回答要简洁、准确。"
            )
        }
    ]

    print("AI Multi-Tool Agent started. Type 'exit' to quit.")

    while True:
        user_input = input("User:").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("AI Multi-Tool Agent stopped.")
            break

        messages.append({
            "role": "user",
            "content": user_input
        })

        answer = chat_with_tools(messages)
        messages.append({
            "role": "assistant",
            "content": answer
        })

        print('AI:', answer)

if __name__ == '__main__':
    main()