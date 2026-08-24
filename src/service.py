"""供 CLI、API 和测试复用的客服服务接口。"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.agent_graph import app


class ChatResult(BaseModel):
    session_id: str
    response: str
    intent: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    needs_human: bool = False
    user_profile: dict[str, Any] = Field(default_factory=dict)


class CustomerServiceAgent:
    async def chat(self, message: str, session_id: str | None = None) -> ChatResult:
        clean_message = message.strip()
        if not clean_message:
            raise ValueError("消息不能为空")
        actual_session_id = session_id or uuid.uuid4().hex
        result = await app.ainvoke(
            {"messages": [HumanMessage(content=clean_message)], "session_id": actual_session_id},
            config={"configurable": {"thread_id": actual_session_id}},
        )
        return ChatResult(
            session_id=actual_session_id,
            response=result["response"],
            intent=result["current_intent"],
            sources=result.get("retrieved_documents", []),
            tool_calls=result.get("tool_calls", []),
            needs_human=result.get("needs_human", False),
            user_profile=result.get("user_profile", {}),
        )
