"""运行确定性的客服质量评测并输出简短报告。"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path

from src.service import CustomerServiceAgent


DATASET = Path(__file__).with_name("dataset.json")


async def evaluate() -> dict[str, float | int]:
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    agent = CustomerServiceAgent()
    intent_hits = answer_hits = tool_hits = source_hits = 0
    tool_cases = source_cases = 0
    started = time.perf_counter()

    for case in cases:
        result = await agent.chat(case["question"], session_id=uuid.uuid4().hex)
        intent_hits += result.intent == case["intent"]
        answer_hits += case["required_text"] in result.response
        if expected_tool := case.get("expected_tool"):
            tool_cases += 1
            tool_hits += any(call["name"] == expected_tool for call in result.tool_calls)
        if case.get("requires_source"):
            source_cases += 1
            source_hits += bool(result.sources)

    count = len(cases)
    return {
        "cases": count,
        "intent_accuracy": round(intent_hits / count, 3),
        "answer_accuracy": round(answer_hits / count, 3),
        "tool_success_rate": round(tool_hits / max(tool_cases, 1), 3),
        "citation_coverage": round(source_hits / max(source_cases, 1), 3),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
    }


if __name__ == "__main__":
    report = asyncio.run(evaluate())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if min(
        report["intent_accuracy"],
        report["answer_accuracy"],
        report["tool_success_rate"],
        report["citation_coverage"],
    ) < 0.9:
        raise SystemExit(1)
