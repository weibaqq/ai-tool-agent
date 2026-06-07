from pathlib import Path

from app.graphs.tool_agent_graph import build_tool_agent_graph

def export_tool_agent_graph() -> None:
    workflow = build_tool_agent_graph()

    output_dir = Path('docs/graphs')
    output_dir.mkdir(parents=True, exist_ok=True)

    mermaid_file = output_dir / "tool_agent_graph.mmd"
    mermaid_png = output_dir / "tool_agent_graph.png"
    mermaid_code = workflow.get_graph().draw_mermaid()
    mermaid_file.write_text(mermaid_code, encoding='utf-8')

    try:
        png_data = workflow.get_graph().draw_mermaid_png()
        mermaid_png.write_bytes(png_data)
    except Exception as e:
        print(f"PNG 导出失败，可忽略：{e}")
    print(f"Mermaid exported to: {mermaid_file}")

if __name__ == "__main__":
    export_tool_agent_graph()