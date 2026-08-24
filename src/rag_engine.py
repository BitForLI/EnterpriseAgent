"""无需外部数据库的混合检索引擎。

BM25 负责关键词相关性，字符 n-gram 余弦相似度改善中文短句召回。
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from src.config import settings


def _terms(text: str) -> list[str]:
    text = text.lower()
    latin = re.findall(r"[a-z0-9]+", text)
    chinese_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    chinese: list[str] = []
    for run in chinese_runs:
        chinese.extend(run[index : index + 2] for index in range(max(1, len(run) - 1)))
    return latin + chinese


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(value * right.get(term, 0) for term, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


@dataclass(frozen=True)
class SearchResult:
    id: str
    title: str
    content: str
    source: str
    score: float

    def to_dict(self) -> dict[str, str | float]:
        return asdict(self)


class RAGEngine:
    def __init__(self, knowledge_path: Path | None = None):
        path = knowledge_path or settings.data_dir / "knowledge_base.json"
        self.documents: list[dict[str, str]] = json.loads(path.read_text(encoding="utf-8"))
        self._doc_terms = [
            _terms(f"{doc['title']} {doc['category']} {doc['content']}")
            for doc in self.documents
        ]
        self._avg_doc_length = sum(map(len, self._doc_terms)) / max(len(self._doc_terms), 1)

    @staticmethod
    def expand_query(query: str) -> str:
        synonyms = {
            "退货": "退换货 退款 售后",
            "退款": "退款 退换货 到账",
            "快递": "物流 配送 发货",
            "保修": "质保 维修 售后",
            "会员": "会员 积分 优惠",
        }
        additions = [words for key, words in synonyms.items() if key in query]
        return " ".join([query, *additions])

    def _bm25(self, query_terms: list[str], document_terms: list[str]) -> float:
        frequencies = Counter(document_terms)
        score = 0.0
        k1, b = 1.5, 0.75
        for term in set(query_terms):
            containing = sum(term in terms for terms in self._doc_terms)
            idf = math.log(1 + (len(self._doc_terms) - containing + 0.5) / (containing + 0.5))
            frequency = frequencies.get(term, 0)
            denominator = frequency + k1 * (
                1 - b + b * len(document_terms) / max(self._avg_doc_length, 1)
            )
            if denominator:
                score += idf * frequency * (k1 + 1) / denominator
        return score

    def retrieve(self, query: str, top_k: int = 3) -> list[SearchResult]:
        query_terms = _terms(self.expand_query(query))
        query_counter = Counter(query_terms)
        scored: list[tuple[float, dict[str, str]]] = []
        raw_bm25 = [self._bm25(query_terms, terms) for terms in self._doc_terms]
        max_bm25 = max(raw_bm25, default=1.0) or 1.0
        for document, document_terms, bm25 in zip(
            self.documents, self._doc_terms, raw_bm25, strict=True
        ):
            score = 0.7 * (bm25 / max_bm25) + 0.3 * _cosine(
                query_counter, Counter(document_terms)
            )
            if score >= 0.08:
                scored.append((score, document))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            SearchResult(
                id=document["id"],
                title=document["title"],
                content=document["content"],
                source=document["source"],
                score=round(score, 4),
            )
            for score, document in scored[:top_k]
        ]

    def retrieve_with_hyde(self, query: str, top_k: int = 3) -> list[SearchResult]:
        """保留原接口名；本地查询扩展承担轻量 HyDE 的作用。"""
        return self.retrieve(query, top_k=top_k)
