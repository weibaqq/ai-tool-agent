from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        description="会话 ID，用于区分不同用户或不同对话"
    )
    message: str = Field(
        min_length=1,
        description="用户输入内容"
    )


class ChatResponse(BaseModel):
    session_id: str = Field(
        min_length=1,
        description="会话 ID，用于区分不同用户或不同对话"
    )
    answer: str = Field(
        description="AI 回复内容"
    )