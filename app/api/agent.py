from fastapi import APIRouter, Request, status
from app.core.exception import AIServiceException, ValidationException
from app.core.response import ApiResponse, success_response
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_service import (
    chat_with_agent_session,
    clear_agent_session,
)

router = APIRouter(
    prefix='/api/agent',
    tags=['Agent']
)


@router.post(
    '/chat',
    response_model=ApiResponse[AgentChatResponse],
    summary="LangGraph Agent 多轮对话 API",
)
async def agent_chat(
        request_body: AgentChatRequest,
        request: Request,
) -> ApiResponse[AgentChatResponse]:
    try:
        answer = await chat_with_agent_session(
            session_id=request_body.session_id,
            user_message=request_body.message,
        )
        return success_response(
            data=AgentChatResponse(
                session_id=request_body.session_id,
                answer=answer,
            ),
            request_id=getattr(request.state, 'request_id', None),
        )
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    except Exception as exc:
        raise AIServiceException(str(exc)) from exc

@router.delete(
    '/session/{session_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清空 LangGraph Agent 会话",
)
async def agent_session_delete(session_id: str):
    try:
        await clear_agent_session(session_id)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc