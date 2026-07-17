import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", text.lower())


class CareerRetriever:
    """Small replaceable retrieval boundary for Career Coach context."""

    def retrieve(self, query: str, documents: list[str], limit: int = 3) -> list[str]:
        query_terms = Counter(_tokens(query))
        scored = []
        for document in documents:
            terms = Counter(_tokens(document))
            score = sum(query_terms[token] * terms[token] for token in query_terms)
            if score:
                scored.append((score, document))
        return [document for _, document in sorted(scored, reverse=True)[:limit]]

