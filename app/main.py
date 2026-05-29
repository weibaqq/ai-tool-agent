from fastapi import FastAPI
from app.api.chat import router as chat_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Tool Agent API",
        description="第一阶段 AI Tool Agent 的 FastAPI 服务版",
        version="0.1.0",
    )

    app.include_router(chat_router)
    return app

app = create_app()