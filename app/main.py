from app.main2.chat_main import run_tool_chat
from app.main2.stream_main import run_stream_chat
from app.main2.structured_output_main import run_structured_output



def main():
    while True:
        print("\n请选择模式：")
        print("1. Tool Chat")
        print("2. Streaming Chat")
        print("3. Structured Output")
        print("0. Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            run_tool_chat()
        elif choice == "2":
            run_stream_chat()
        elif choice == "3":
            run_structured_output()
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("无效选项，请重新输入。")

if __name__ == "__main__":
        main()
