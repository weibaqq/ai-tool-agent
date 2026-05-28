from typing import Any

from app.llm.stream_client import stream_chat


def run_stream_chat() -> None:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "你是一个专业、耐心的 AI 应用开发助手。"
        }
    ]

    print("AI Streaming Chat started. Type 'exit' to quit.")

    while True:
        user_input = input("\nUser: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        if not user_input:
            continue

        messages.append({
            "role": "user",
            "content": user_input,
        })

        print("AI: ", end="", flush=True)

        assistant_reply = ''
        try:
            for token in stream_chat(messages):
                print(token, end="", flush=True)
                assistant_reply += token
        except Exception as exc:
            print(f"\nError: {exc}")
            continue

        print()

        messages.append({
            "role": "assistant",
            "content": assistant_reply,
        })
