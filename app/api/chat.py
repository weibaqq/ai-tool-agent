from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_once

router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI Tool Agent Chat API",
)
def chat(request: ChatRequest)-> ChatResponse:
    try:
        answer = chat_once(request.message)
        return ChatResponse(answer=answer)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI 服务调用失败：{exc}",
        ) from exc