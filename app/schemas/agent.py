from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        description="会话 ID，用于区分不同 Agent 对话"
    )
    message: str = Field(
        min_length=1,
        description="用户输入内容"
    )


class AgentChatResponse(BaseModel):
    session_id: str = Field(
        min_length=1,
        description="会话 ID，用于区分不同用户或不同对话"
    )
    answer: str = Field(
        description="AI 回复内容"
    )
