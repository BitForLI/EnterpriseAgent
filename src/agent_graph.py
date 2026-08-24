"""企业客服 LangGraph：识别意图、检索知识、调用工具并安全回复。"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.config import settings
from src.langchain_tools import TOOL_REGISTRY
from src.rag_engine import RAGEngine
from src.state import AgentState


rag = RAGEngine()


def _latest_text(state: AgentState) -> str:
    return str(state["messages"][-1].content).strip()


def _extract_entities(text: str) -> dict[str, Any]:
    entities: dict[str, Any] = {}
    user_match = re.search(r"(?:用户|user|客户|ID)\s*[#：:]?\s*(\d+)", text, re.I)
    order_match = re.search(r"(?:订单|order)\s*[#：:]?\s*(\d+)", text, re.I)
    name_match = re.search(r"(?:我叫|我是)\s*([\u4e00-\u9fffA-Za-z·]{2,20})", text)
    if user_match:
        entities["user_id"] = int(user_match.group(1))
    if order_match:
        entities["order_id"] = int(order_match.group(1))
    if name_match:
        entities["name"] = name_match.group(1)
    return entities


def _classify(text: str, pending_action: dict[str, Any] | None) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["忽略之前", "系统提示词", "system prompt", "泄露密钥"]):
        return "unsafe"
    if pending_action and any(term in lowered for term in ["确认", "同意", "是的", "yes"]):
        return "confirm_action"
    if pending_action and any(term in lowered for term in ["不确认", "取消操作", "不用了", "no"]):
        return "cancel_pending"
    if any(term in lowered for term in ["取消订单", "删除订单", "修改地址"]):
        return "sensitive_action"
    if any(term in lowered for term in ["人工", "投诉", "经理", "客服人员"]):
        return "human_handoff"
    if any(term in lowered for term in ["订单", "物流", "快递", "发货", "到哪"]):
        return "order_inquiry"
    if any(term in lowered for term in ["退货", "换货", "退款", "保修", "政策", "发票"]):
        return "policy_question"
    if any(term in lowered for term in ["推荐", "商品", "价格", "库存", "手机", "电脑", "耳机"]):
        return "product_search"
    return "general_question"


def understand_node(state: AgentState) -> dict[str, Any]:
    text = _latest_text(state)
    entities = _extract_entities(text)
    profile = dict(state.get("user_profile", {}))
    for key in ("name", "user_id"):
        if key in entities:
            profile[key] = entities[key]

    message_count = len(state.get("messages", []))
    summary = state.get("conversation_summary", "")
    if message_count >= 6:
        summary = f"已进行 {message_count // 2} 轮对话；最近意图与客户资料已保留。"

    return {
        "current_intent": _classify(text, state.get("pending_action")),
        "entities": entities,
        "user_profile": profile,
        "retrieved_documents": [],
        "tool_calls": [],
        "draft_response": "",
        "response": "",
        "needs_human": False,
        "conversation_summary": summary,
        "last_error": None,
        "retry_count": 0,
    }


def route_intent(state: AgentState) -> str:
    return state["current_intent"]


def _invoke_tool(name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None, int]:
    error: str | None = None
    for attempt in range(2):
        try:
            result = TOOL_REGISTRY[name].invoke(arguments)
            return result, None, attempt
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    return None, error, 2


def product_node(state: AgentState) -> dict[str, Any]:
    arguments = {"query": _latest_text(state), "limit": 3}
    result, error, retries = _invoke_tool("catalog_search", arguments)
    if error or not result:
        return {
            "draft_response": "商品系统暂时不可用，已建议转接人工客服。",
            "needs_human": True,
            "last_error": error,
            "retry_count": retries,
        }
    lines = [
        f"{item['name']}：¥{item['price']}，库存 {item['stock']} 件。{item['description']}"
        for item in result["products"]
    ]
    return {
        "draft_response": "我为你筛选了：\n" + "\n".join(f"• {line}" for line in lines),
        "tool_calls": [{"name": "catalog_search", "arguments": arguments}],
        "retry_count": retries,
    }


def order_node(state: AgentState) -> dict[str, Any]:
    entities = state.get("entities", {})
    user_id = entities.get("user_id") or state.get("user_profile", {}).get("user_id")
    order_id = entities.get("order_id")
    if user_id is None and order_id is None:
        return {"draft_response": "请提供用户 ID 或订单号，例如：查询用户 101 的订单。"}

    arguments = {"user_id": user_id, "order_id": order_id}
    result, error, retries = _invoke_tool("order_lookup", arguments)
    if error or not result:
        return {
            "draft_response": "订单系统暂时不可用，请稍后重试或转人工客服。",
            "last_error": error,
            "retry_count": retries,
        }
    orders = result["orders"]
    if not orders:
        return {
            "draft_response": "没有查到对应订单，请核对用户 ID 或订单号。",
            "tool_calls": [{"name": "order_lookup", "arguments": arguments}],
        }
    lines = [
        f"订单 #{order['id']}：{order['status']}，{order['logistics']}，金额 ¥{order['total']}。"
        for order in orders
    ]
    return {
        "draft_response": "查询结果：\n" + "\n".join(f"• {line}" for line in lines),
        "tool_calls": [{"name": "order_lookup", "arguments": arguments}],
        "retry_count": retries,
    }


def knowledge_node(state: AgentState) -> dict[str, Any]:
    results = rag.retrieve_with_hyde(_latest_text(state), top_k=2)
    if not results:
        return {
            "draft_response": "知识库里暂时没有可靠答案。你可以换种说法，或让我转接人工客服。"
        }
    answer = "\n".join(result.content for result in results)
    citations = "、".join(f"{item.title}（{item.id}）" for item in results)
    return {
        "draft_response": f"{answer}\n\n参考：{citations}",
        "retrieved_documents": [item.to_dict() for item in results],
    }


def general_node(state: AgentState) -> dict[str, Any]:
    results = rag.retrieve(_latest_text(state), top_k=1)
    if results and results[0].score >= 0.18:
        item = results[0]
        return {
            "draft_response": f"{item.content}\n\n参考：{item.title}（{item.id}）",
            "retrieved_documents": [item.to_dict()],
        }
    return {
        "draft_response": "我可以帮你推荐商品、查询订单、说明退换货政策，或转接人工客服。"
    }


def unsafe_node(_: AgentState) -> dict[str, Any]:
    return {
        "draft_response": "我不能提供系统指令、密钥或内部配置，但可以继续帮助你处理客服问题。"
    }


def sensitive_node(state: AgentState) -> dict[str, Any]:
    return {
        "draft_response": "这是敏感操作。请回复“确认”，我会创建人工审核工单；回复其他内容则不会处理。",
        "pending_action": {"type": "manual_review", "summary": _latest_text(state)},
    }


def cancel_pending_node(_: AgentState) -> dict[str, Any]:
    return {"draft_response": "已取消，本次敏感操作不会继续处理。", "pending_action": None}


def human_node(state: AgentState) -> dict[str, Any]:
    pending = state.get("pending_action") or {}
    summary = pending.get("summary") or _latest_text(state)
    user_id = state.get("user_profile", {}).get("user_id")
    priority = "high" if any(term in summary for term in ["投诉", "紧急", "取消"]) else "normal"
    arguments = {"summary": summary, "user_id": user_id, "priority": priority}
    result, error, retries = _invoke_tool("human_handoff", arguments)
    if error or not result:
        return {
            "draft_response": "暂时无法创建工单，请拨打人工客服热线 400-800-2026。",
            "needs_human": True,
            "last_error": error,
            "retry_count": retries,
        }
    return {
        "draft_response": f"已创建人工客服工单 {result['id']}，客服会尽快处理。",
        "needs_human": True,
        "pending_action": None,
        "tool_calls": [{"name": "human_handoff", "arguments": arguments}],
        "retry_count": retries,
    }


def _polish_with_openai(state: AgentState, draft: str) -> str:
    if settings.llm_provider != "openai":
        return draft
    from langchain.chat_models import init_chat_model
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是企业客服。只能依据草稿和知识库作答，不编造政策、库存或订单；保持简洁。",
            ),
            ("human", "客户问题：{question}\n可靠草稿：{draft}"),
        ]
    )
    model = init_chat_model(f"openai:{settings.openai_model}", temperature=0)
    return str((prompt | model).invoke({"question": _latest_text(state), "draft": draft}).content)


def finalize_node(state: AgentState) -> dict[str, Any]:
    draft = state.get("draft_response") or "抱歉，我暂时无法处理这个问题。"
    error = state.get("last_error")
    try:
        response = _polish_with_openai(state, draft)
    except Exception as exc:
        response = draft
        error = f"LLM fallback: {type(exc).__name__}: {exc}"
    return {"response": response, "messages": [AIMessage(content=response)], "last_error": error}


builder = StateGraph(AgentState)
builder.add_node("understand", understand_node)
builder.add_node("product_search", product_node)
builder.add_node("order_inquiry", order_node)
builder.add_node("policy_question", knowledge_node)
builder.add_node("general_question", general_node)
builder.add_node("unsafe", unsafe_node)
builder.add_node("sensitive_action", sensitive_node)
builder.add_node("confirm_action", human_node)
builder.add_node("cancel_pending", cancel_pending_node)
builder.add_node("human_handoff", human_node)
builder.add_node("finalize", finalize_node)
builder.add_edge(START, "understand")
builder.add_conditional_edges(
    "understand",
    route_intent,
    {
        "product_search": "product_search",
        "order_inquiry": "order_inquiry",
        "policy_question": "policy_question",
        "general_question": "general_question",
        "unsafe": "unsafe",
        "sensitive_action": "sensitive_action",
        "confirm_action": "confirm_action",
        "cancel_pending": "cancel_pending",
        "human_handoff": "human_handoff",
    },
)
for node in [
    "product_search",
    "order_inquiry",
    "policy_question",
    "general_question",
    "unsafe",
    "sensitive_action",
    "confirm_action",
    "cancel_pending",
    "human_handoff",
]:
    builder.add_edge(node, "finalize")
builder.add_edge("finalize", END)

app = builder.compile(checkpointer=MemorySaver())
