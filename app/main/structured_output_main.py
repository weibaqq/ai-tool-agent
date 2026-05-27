from app.llm.structured_client import analyze_text


def main() -> None:
    print("Structured Output Demo started. Type 'exit' to quit.")

    while True:
        user_input = input("User: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        if not user_input:
            continue

        try:
            result = analyze_text(user_input)
        except Exception as exc:
            print("Error:", exc)
            continue
        print("Summary:", result.summary)
        print("Sentiment:", result.sentiment.value)
        print("Keywords:", ", ".join(result.keywords))
        print("Action Required:", result.action_required)

if __name__ == "__main__":
    main()