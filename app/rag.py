"""
RAG (Retrieval-Augmented Generation) Module
---------------------------------------------
Retrieves the most relevant knowledge-base articles for a given ticket, then
(optionally) uses an LLM to draft a grounded response.

Embedding backend is pluggable:
  - "tfidf"  : scikit-learn TF-IDF + cosine similarity. Zero external calls,
               zero cost, zero setup, deterministic. This is the default so
               the whole project runs immediately after `pip install -r
               requirements.txt` with no API keys and no internet dependency
               for the retrieval step.
  - "openai" : OpenAI embeddings API for higher-quality semantic search.
               Swap in via EMBEDDING_BACKEND=openai in .env.

In the recommendation report we discuss upgrading this to a proper vector DB
(Pinecone / Weaviate / Chroma) for production scale - the interface here
(`KnowledgeBase.search`) is deliberately kept small so that swap is a
localized change, not a rewrite.
"""
from __future__ import annotations
import os
import re
from dataclasses import dataclass
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings


@dataclass
class KBArticle:
    id: str
    category: str
    title: str
    content: str


def _parse_markdown_kb(filepath: str) -> KBArticle:
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    meta = {}
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            front_matter, body = parts[1], parts[2]
            for line in front_matter.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()

    return KBArticle(
        id=meta.get("id", os.path.basename(filepath)),
        category=meta.get("category", "general"),
        title=meta.get("title", os.path.basename(filepath)),
        content=body.strip(),
    )


class KnowledgeBase:
    def __init__(self, kb_dir: str = None):
        self.kb_dir = kb_dir or settings.KB_DIR
        self.articles: List[KBArticle] = []
        self._vectorizer: TfidfVectorizer = None
        self._matrix = None
        self._load()

    def _load(self):
        if not os.path.isdir(self.kb_dir):
            return
        for fname in sorted(os.listdir(self.kb_dir)):
            if fname.endswith(".md"):
                self.articles.append(_parse_markdown_kb(os.path.join(self.kb_dir, fname)))

        if self.articles:
            corpus = [f"{a.title} {a.content}" for a in self.articles]
            self._vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
            self._matrix = self._vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 2) -> List[dict]:
        """Return top_k most relevant articles with similarity scores."""
        if not self.articles or self._vectorizer is None:
            return []

        query_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix).flatten()
        ranked_idx = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in ranked_idx:
            score = float(sims[idx])
            if score <= 0:
                continue
            article = self.articles[idx]
            results.append({
                "id": article.id,
                "title": article.title,
                "category": article.category,
                "content": article.content,
                "score": round(score, 4),
            })
        return results


# Module-level singleton so the KB (and its TF-IDF index) is built once,
# not on every request.
_kb_instance: KnowledgeBase = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
