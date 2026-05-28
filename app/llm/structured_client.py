import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import BadRequestError, OpenAI
from pydantic import ValidationError

from app.schemas.analysis import TextAnalysisResult
from app.config import get_settings

settings = get_settings()

load_dotenv()

client = OpenAI(
    api_key=settings.api_key,
    base_url=settings.base_url,
)

model = settings.model

# DeepSeek API 支持的 response_format 选项：
#
# ✅ {"type": "json_object"} - 强制输出合法 JSON
#
# ❌ {"type": "json_schema"} - 不支持（这是 OpenAI 的格式）

_ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "json_object",
    "json_object": {
        "name": "text_analysis_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "用一句话总结用户输入内容",
                },
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral", "mixed"],
                    "description": "文本情绪倾向",
                },
                "keywords": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "从文本中提取的关键词，最多5个",
                },
                "action_required": {
                    "type": "boolean",
                    "description": "是否需要后续人工处理",
                }
            },
            "required": ["summary", "sentiment", "keywords", "action_required"],
            "additionalProperties": False,
        }
    }
}

def analyze_text(text: str) -> TextAnalysisResult:
    if not text.strip():
        raise ValueError("text 不能为空")

    messages = [
        {
            "role": "system",
            "content": (
                "你是一个文本分析助手。"
                "你必须只返回一个 JSON 对象，不要输出 Markdown，不要输出解释。"
                "JSON 必须包含字段：summary(string), sentiment(positive/negative/neutral/mixed), "
                "keywords(string 数组，最多5个), action_required(boolean)。"
            )
        },
        {
            "role": "user",
            "content": text
        }
    ]

    try:
        res = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=_ANALYSIS_SCHEMA,
            temperature=settings.temperature,
        )
    except BadRequestError as exc:
        if "response_format" not in str(exc):
            raise
        res = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=settings.temperature,
        )

    content = res.choices[0].message.content

    if not content:
        raise RuntimeError("模型没有返回内容")

    try:
        data = json.loads(content)
        result = TextAnalysisResult.model_validate(data)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"模型返回的不是合法 JSON: {content}") from exc
    except ValidationError as exc:
        raise RuntimeError(f"模型返回结构不符合 Schema: {exc}") from exc

    return result
