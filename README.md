# Enterprise Customer Service Agent

一个可本地完整运行的企业客服 Agent。项目聚焦业务智能，而不是云基础设施：使用 LangGraph 编排客服流程、LangChain 工具调用、本地混合 RAG、MCP 工具服务和人工工单。

## 能力

- 售前商品推荐、库存与价格查询
- 订单和物流查询
- 带来源引用的退换货、退款、保修与发票问答
- 多轮会话记忆和用户资料提取
- 敏感操作二次确认、提示词攻击拦截、工具失败重试
- 投诉与复杂问题转人工，并持久化 SQLite 工单
- FastAPI 接口、响应式聊天网页和命令行模式
- 默认离线运行，也可选择 OpenAI 优化表达
- 同一业务工具同时供 Agent 和 MCP 客户端使用

## 工作流程

```text
用户消息
  -> 意图识别与实体提取
  -> 商品工具 / 订单工具 / 知识库 RAG / 人工工单
  -> 安全边界与失败降级
  -> 带工具记录和知识来源的回复
```

## 快速开始

要求 Python 3.11 或更高版本。

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# Web 模式
python main.py --web
# 浏览器打开 http://127.0.0.1:8000

# 或命令行模式
python main.py
```

默认 `LLM_PROVIDER=local`，无需 API Key。若要使用 OpenAI 对可靠草稿进行语言优化：

```bash
Copy-Item .env.example .env
# 在 .env 中设置 LLM_PROVIDER=openai 和 OPENAI_API_KEY
python main.py --web
```

## MCP 服务

```bash
python -m src.mcp_server
```

工具包括 `search_products`、`lookup_orders` 和 `escalate_to_human`。

## 测试

```bash
python -m pytest -q
python -m evals.run_eval
```

测试覆盖知识检索、商品与订单工具、多轮记忆、敏感操作确认、人工转接和 HTTP API。离线评测额外输出意图准确率、回答准确率、工具成功率和引用覆盖率。

## 示例问题

- `推荐一款适合办公的电脑`
- `查询用户 101 的订单物流`
- `七天内可以退货吗？`
- `我要投诉并转人工客服`
- `取消订单 9001`，然后回复 `确认`

## 项目结构

```text
data/                  模拟商品、订单和客服知识库
src/agent_graph.py     LangGraph 业务编排
src/rag_engine.py      BM25 + 中文字符相似度混合检索
src/langchain_tools.py LangChain 工具
src/mcp_server.py      MCP 服务端
src/api.py             FastAPI 接口
web/index.html         聊天演示页面
tests/                 自动化测试
evals/                 应用级质量评测集
```
