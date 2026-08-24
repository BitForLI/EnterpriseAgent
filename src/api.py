"""FastAPI 与静态聊天页面。"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config import settings
from src.service import ChatResult, CustomerServiceAgent


api = FastAPI(title="Enterprise Customer Service Agent", version="1.0.0")
agent = CustomerServiceAgent()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=100)


@api.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(settings.web_dir / "index.html")


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": settings.llm_provider}


@api.post("/api/chat", response_model=ChatResult)
async def chat(request: ChatRequest) -> ChatResult:
    try:
        return await agent.chat(request.message, session_id=request.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
