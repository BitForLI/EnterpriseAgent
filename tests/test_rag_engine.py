from src.rag_engine import RAGEngine


def test_retrieve_returns_policy_with_source():
    results = RAGEngine().retrieve("商品怎么退款退货？")

    assert results
    assert results[0].id in {"KB-RET-001", "KB-REF-002"}
    assert results[0].source


def test_unknown_query_has_no_strong_match():
    results = RAGEngine().retrieve("量子纠缠实验", top_k=1)

    assert results == []
