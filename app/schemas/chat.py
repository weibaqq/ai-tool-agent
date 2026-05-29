from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="用户输入内容"
    )


class ChatResponse(BaseModel):
    answer: str = Field(
        description="AI 回复内容"
    )