from app.graphs.basic_workflow import build_basic_workflow

def main() -> None:
    workflow = build_basic_workflow()
    print("Basic LangGraph Workflow started. Type 'exit' to quit.")

    while True:
        user_input = input("\nUser: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        if not user_input:
            continue

        result = workflow.invoke({
            'user_input': user_input,
        })

        print("Route:", result["route"])
        print("AI:", result["answer"])

if __name__ == "__main__":
    main()