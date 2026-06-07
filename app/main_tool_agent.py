from langchain_core.messages import AIMessage
from app.graphs.tool_agent_graph import build_tool_agent_graph, build_initial_messages

def main():
    workflow = build_tool_agent_graph()
    print("LangGraph Tool Agent started. Type 'exit' to quit.")
    while True:
        user_input = input("\nUser: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        if not user_input:
            continue

        result = workflow.invoke({
            'messages' : build_initial_messages(user_input),
        })

        final_message = result['messages'][-1]
        if isinstance(final_message, AIMessage):
            print("AI:", final_message.content)
        else:
            print("AI:", final_message)

if __name__ == "__main__":
    main()