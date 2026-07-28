#定义pydantic状态与对话记忆模型

from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class AgentState(BaseModel):
    # 自动将新的对话消息追加到历史记录中
    messages: Annotated[list, add_messages] = []

    # 路由识别出的当前意图
    current_intent: Optional[str] = None

    # 对话中实时提取的用户画像与上下文
    user_profile: Dict[str, Any] = Field(default_factory=dict)

    # 用于自愈循环的错误追踪字段
    last_error: Optional[str] = None
    retry_count: int = 0