from pathlib import Path

from graphs.basic_workflow import build_basic_workflow


def export_mermaid() -> None:
    workflow = build_basic_workflow()

    mermaid_code = workflow.get_graph().draw_mermaid()

    output_dir = Path("docs/graphs")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "basic_workflow.mmd"
    output_file.write_text(mermaid_code, encoding="utf-8")

    print(f"Mermaid graph exported to: {output_file}")


if __name__ == "__main__":
    export_mermaid()