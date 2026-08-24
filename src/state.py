"""LangGraph 共享状态定义。"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str
    current_intent: str
    user_profile: dict[str, Any]
    entities: dict[str, Any]
    retrieved_documents: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    draft_response: str
    response: str
    needs_human: bool
    pending_action: dict[str, Any] | None
    conversation_summary: str
    last_error: str | None
    retry_count: int
