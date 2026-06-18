import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.agent import router as agent_router
from app.api.checkpoint_agent import router as checkpoint_agent_router
from app.api.hil_agent import router as hil_agent_router
from app.api.multi_approval_agent import router as multi_approval_agent_router
from app.core.exception import AppException, ValidationException
from app.core.middleware import request_context_middleware
from app.core.response import error_message
from app.db.postgres import init_postgres_schema
from app.graphs.checkpoint_agent_runner import checkpoint_agent_runner
from app.graphs.hil_agent_runner import hil_agent_runner
from app.graphs.multi_approval_runner import multi_approval_runner

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_postgres_schema()
    yield
    checkpoint_agent_runner.close()
    hil_agent_runner.close()
    multi_approval_runner.close()

def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="AI Tool Agent API",
        description="AI Tool Agent FastAPI + LangGraph Service",
        version="0.3.0",
        lifespan=lifespan,
    )
    app.middleware("http")(request_context_middleware)
    app.include_router(chat_router)
    app.include_router(health_router)
    app.include_router(agent_router)
    app.include_router(hil_agent_router)
    app.include_router(multi_approval_agent_router)
    app.include_router(checkpoint_agent_router)
    register_exception_handlers(app)

    return app

def _get_request_id(request: Request) -> str | None:
    return getattr(request, "request_id", None)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
            request: Request, exc: AppException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_message(
                message=exc.message,
                request_id=_get_request_id(request),
            ).model_dump(),
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(
            request: Request, exc: ValidationException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_message(
                message=exc.message,
                request_id=_get_request_id(request),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def exception_handler(
            request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_message(
                message='服务器内部错误',
                request_id=_get_request_id(request),
            ).model_dump(),
        )


app = create_app()
