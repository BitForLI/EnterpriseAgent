#LangGraph路由编排与工作节点

from langgraph.graph import StateGraph, END
from langchain.chat_models import init_chat_model
from src.state import AgentState

# 初始化统一模型
llm = init_chat_model("openai:gpt-4o-mini")

# 1. 意图识别 Router 节点
def router_node(state: AgentState):
    # 利用 LLM 或分类逻辑推断用户意图
    user_input = state.messages[-1].content
    # 假设这里判断出了意图
    return {"current_intent": "order_inquiry"}

# 2. 条件路由逻辑
def route_intent(state: AgentState):
    if state.current_intent == "order_inquiry":
        return "support_worker"
    return "sales_worker"

# 3. 各种 Worker 节点
def support_worker(state: AgentState):
    # 售后 Agent 节点逻辑，绑定 MCP 调用的工具
    return {"messages": [{"role": "assistant", "content": "已为您查询售后状态..."}]}

# 构建图
builder = StateGraph(AgentState)
builder.add_node("router", router_node)
builder.add_node("support_worker", support_worker)


builder.set_entry_point("router")
builder.add_conditional_edges("router", route_intent)
builder.add_edge("support_worker", END)

# 编译图应用
app = builder.compile()