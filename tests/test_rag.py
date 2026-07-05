import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag import KnowledgeBase


def test_kb_loads_articles():
    kb = KnowledgeBase()
    assert len(kb.articles) >= 5


def test_search_returns_relevant_billing_article():
    kb = KnowledgeBase()
    results = kb.search("I was charged twice for my order", top_k=2)
    assert len(results) > 0
    assert any(r["category"] == "billing" for r in results)


def test_search_returns_relevant_shipping_article():
    kb = KnowledgeBase()
    results = kb.search("my package tracking is not updating", top_k=2)
    assert len(results) > 0
    assert any(r["category"] == "shipping" for r in results)


def test_search_empty_query_does_not_crash():
    kb = KnowledgeBase()
    results = kb.search("asdkjaslkdjaslkdj qqzxcvqqzxcv", top_k=2)
    assert isinstance(results, list)
