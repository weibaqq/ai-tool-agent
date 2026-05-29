from fastapi import APIRouter, HTTPException,status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_with_session,clear_session

router = APIRouter(
    prefix="/api",
    tags=["Chat"],
)

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="多轮对话 Chat API",
)
def chat(request: ChatRequest)-> ChatResponse:
    try:
        answer = chat_with_session(request.session_id, request.message)
        return ChatResponse(session_id=request.session_id, answer=answer)
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

@router.delete(
    '/sessions/{session_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清空指定会话",
)
def delete_session(session_id:str) -> None:
    if not session_id.strip():
        raise ValueError("session_id <UNK>")
    try:
        clear_session(session_id)
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
