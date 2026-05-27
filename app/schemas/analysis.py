from enum import Enum
from pydantic import BaseModel, Field

class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    mixed = "mixed"

class TextAnalysisResult(BaseModel):
    summary: str = Field(
        description="用一句话总结用户输入的内容",
    )
    sentiment: Sentiment = Field(
        description="文本情绪倾向",
    )
    keywords: list[str] = Field(
        description="从文本中提取的关键词，最多5个",
    )
    action_required: bool = Field(
        description="是否需要后续人工处理",
    )