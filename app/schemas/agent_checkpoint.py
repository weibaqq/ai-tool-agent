from pydantic import BaseModel, Field


class CheckpointAgentChatRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        description="LangGraph thread ID，用于 checkpoint 保存和恢复",
    )
    message: str = Field(
        min_length=1,
        description="用户输入内容",
    )


class CheckpointAgentChatResponse(BaseModel):
    thread_id: str = Field(description="LangGraph thread ID")
    answer: str = Field(description="Agent 最终回答")

class CheckpointAgentStateResponse(BaseModel):
    thread_id: str = Field(description="LangGraph thread ID")
    message_count: int = Field(description="当前 state 中消息数量")
    next_nodes: list[str] = Field(description="下一步待执行节点")