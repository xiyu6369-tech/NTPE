"""Foundation-08.6 storage-agnostic semantic index."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from ..contracts import KnowledgeItem, KnowledgeQuery
from .ranking import KnowledgeRankingEngine, KnowledgeSearchResult
from .tokenizer import KnowledgeTokenizer


@dataclass
class KnowledgeIndexDocument:
    """Internal indexed document representation."""

    item: KnowledgeItem
    tokens: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"item": self.item.to_dict(), "tokens": list(self.tokens)}


class KnowledgeSemanticIndex:
    """Dependency-free semantic index contract and default implementation.

    This implementation behaves as a deterministic hybrid keyword/semantic
    layer. Future vector, SQLite FTS, or external search backends can implement
    the same public methods without changing callers.
    """

    version = "foundation-08.6"

    def __init__(self, tokenizer: Optional[KnowledgeTokenizer] = None, ranking: Optional[KnowledgeRankingEngine] = None, metadata: Optional[Dict[str, Any]] = None):
        self.tokenizer = tokenizer or KnowledgeTokenizer()
        self.ranking = ranking or KnowledgeRankingEngine()
        self.metadata = dict(metadata or {})
        self._documents: Dict[Tuple[str, str], KnowledgeIndexDocument] = {}
        self._inverted: Dict[str, Set[Tuple[str, str]]] = {}

    def _doc_id(self, item: KnowledgeItem) -> Tuple[str, str]:
        return (item.domain, item.key)

    def add(self, item: KnowledgeItem | Dict[str, Any]) -> KnowledgeItem:
        knowledge_item = item if isinstance(item, KnowledgeItem) else KnowledgeItem.from_dict(item)
        doc_id = self._doc_id(knowledge_item)
        self.remove(knowledge_item.key, knowledge_item.domain)
        tokens = self.tokenizer.item_tokens(knowledge_item)
        self._documents[doc_id] = KnowledgeIndexDocument(item=knowledge_item, tokens=tokens)
        for token in tokens:
            self._inverted.setdefault(token, set()).add(doc_id)
        return knowledge_item

    def add_many(self, items: Iterable[KnowledgeItem | Dict[str, Any]]) -> List[KnowledgeItem]:
        return [self.add(item) for item in items]

    def remove(self, key: str, domain: str = "general") -> bool:
        doc_id = (domain, key)
        document = self._documents.pop(doc_id, None)
        if document is None:
            return False
        for token in document.tokens:
            refs = self._inverted.get(token)
            if refs is not None:
                refs.discard(doc_id)
                if not refs:
                    self._inverted.pop(token, None)
        return True

    def clear(self) -> None:
        self._documents.clear()
        self._inverted.clear()

    def build(self, items: Iterable[KnowledgeItem | Dict[str, Any]]) -> "KnowledgeSemanticIndex":
        self.clear()
        self.add_many(items)
        return self

    def search(self, text: str = "", domain: Optional[str] = None, limit: Optional[int] = None, query: Optional[KnowledgeQuery] = None) -> List[KnowledgeSearchResult]:
        if query is not None:
            text = query.text or text
            domain = query.domain or domain
            limit = query.limit if query.limit is not None else limit
        query_tokens = self.tokenizer.tokenize(text)
        candidate_ids: Set[Tuple[str, str]] = set()
        for token in query_tokens:
            candidate_ids.update(self._inverted.get(token, set()))
        if not query_tokens:
            candidate_ids = set(self._documents.keys())

        results: List[KnowledgeSearchResult] = []
        for doc_id in candidate_ids:
            document = self._documents.get(doc_id)
            if document is None:
                continue
            item = document.item
            if domain and item.domain != domain:
                continue
            if query is not None and not query.matches(item):
                # KnowledgeQuery text matching can be stricter than token matching.
                # For semantic search, allow token matches even when substring check fails,
                # but still enforce keys/domain/metadata.
                if query.domain and item.domain != query.domain:
                    continue
                if query.keys and item.key not in query.keys:
                    continue
                if query.metadata and any(item.metadata.get(k) != v for k, v in query.metadata.items()):
                    continue
            score, matched = self.ranking.score(query_tokens, document.tokens, item=item, query_text=text)
            if query_tokens and score <= 0:
                continue
            results.append(KnowledgeSearchResult(item=item, score=score, matched_tokens=matched, metadata={"version": self.version}))
        return self.ranking.rank(results, limit=limit)

    def query(self, query: Optional[KnowledgeQuery] = None) -> List[KnowledgeItem]:
        return [result.item for result in self.search(query=query or KnowledgeQuery())]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "metadata": dict(self.metadata),
            "documents": [document.to_dict() for document in self._documents.values()],
            "token_count": len(self._inverted),
            "document_count": len(self._documents),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "KnowledgeSemanticIndex":
        index = cls(metadata=dict(payload.get("metadata") or {}))
        for document in payload.get("documents", []):
            item = KnowledgeItem.from_dict(document.get("item") or {})
            index.add(item)
        return index

    def manifest(self) -> Dict[str, Any]:
        return {
            "name": "knowledge_semantic_index",
            "version": self.version,
            "enabled": True,
            "capabilities": ["index", "tokenize", "search", "hybrid_search", "rank", "serialize"],
            "metadata": {"document_count": len(self._documents), "token_count": len(self._inverted), **self.metadata},
        }


__all__ = ["KnowledgeIndexDocument", "KnowledgeSemanticIndex"]
