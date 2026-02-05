"""
Knowledge Engine
================
Main knowledge engine that combines indexing and searching.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import threading

from core.logging import app_logger
from .indexer import KnowledgeIndexer, IndexStats, create_default_indexer
from .searcher import KnowledgeSearcher, SearchResult, SearchOptions
from .sources import KnowledgeItem, KnowledgeSource, SourceType


@dataclass
class KnowledgeQuery:
    """A knowledge query with context."""
    text: str
    source_types: Optional[List[SourceType]] = None
    max_results: int = 5
    include_context: bool = True


@dataclass
class KnowledgeResponse:
    """Response from the knowledge engine."""
    query: str
    results: List[SearchResult]
    context_text: str
    processing_time_ms: float
    total_indexed: int


class KnowledgeEngine:
    """
    Main knowledge engine for AI Copilot.

    Combines indexing and searching to provide relevant context for AI queries.

    Features:
    - Auto-indexing of application knowledge
    - Fast text-based search
    - Context building for AI prompts
    - Support for Arabic and English

    Usage:
        engine = get_knowledge_engine()
        engine.initialize()

        # Search
        response = engine.query("كيف أضيف موظف جديد؟")
        print(response.context_text)

        # Get context for AI
        context = engine.get_context_for_prompt("أريد تقرير الرواتب")
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._indexer: Optional[KnowledgeIndexer] = None
        self._searcher: Optional[KnowledgeSearcher] = None
        self._ready = False
        self._init_lock = threading.RLock()

        self._initialized = True

    def initialize(self, auto_index: bool = True) -> bool:
        """
        Initialize the knowledge engine.

        Args:
            auto_index: Whether to automatically index on startup

        Returns:
            True if successful
        """
        with self._init_lock:
            if self._ready:
                return True

            try:
                # Create default indexer with sources
                self._indexer = create_default_indexer()

                # Create searcher
                self._searcher = KnowledgeSearcher()

                # Index if requested
                if auto_index:
                    self._indexer.index_all()
                    self._searcher.set_items(self._indexer.get_all_items())

                self._ready = True
                app_logger.info("Knowledge engine initialized")
                return True

            except Exception as e:
                app_logger.error(f"Failed to initialize knowledge engine: {e}")
                return False

    def is_ready(self) -> bool:
        """Check if the engine is ready."""
        return self._ready

    def add_source(self, source: KnowledgeSource) -> None:
        """Add a knowledge source."""
        if self._indexer:
            self._indexer.add_source(source)

    def reindex(self) -> IndexStats:
        """Reindex all knowledge sources."""
        if not self._indexer or not self._searcher:
            return IndexStats()

        stats = self._indexer.index_all()
        self._searcher.set_items(self._indexer.get_all_items())
        return stats

    def query(self, query: KnowledgeQuery | str) -> KnowledgeResponse:
        """
        Query the knowledge base.

        Args:
            query: The query (string or KnowledgeQuery)

        Returns:
            Knowledge response with results and context
        """
        import time
        start_time = time.time()

        # Convert string to query object
        if isinstance(query, str):
            query = KnowledgeQuery(text=query)

        if not self._ready or not self._searcher:
            return KnowledgeResponse(
                query=query.text,
                results=[],
                context_text="",
                processing_time_ms=0.0,
                total_indexed=0
            )

        # Search
        options = SearchOptions(
            max_results=query.max_results,
            source_types=query.source_types
        )
        results = self._searcher.search(query.text, options)

        # Build context text
        context_text = ""
        if query.include_context and results:
            context_text = self._build_context(results)

        processing_time = (time.time() - start_time) * 1000

        return KnowledgeResponse(
            query=query.text,
            results=results,
            context_text=context_text,
            processing_time_ms=processing_time,
            total_indexed=len(self._indexer.get_all_items()) if self._indexer else 0
        )

    def get_context_for_prompt(
        self,
        user_query: str,
        max_items: int = 3,
        max_length: int = 2000
    ) -> str:
        """
        Get relevant context for an AI prompt.

        Args:
            user_query: The user's query
            max_items: Maximum number of items to include
            max_length: Maximum context length in characters

        Returns:
            Context text to include in AI prompt
        """
        response = self.query(KnowledgeQuery(
            text=user_query,
            max_results=max_items,
            include_context=True
        ))

        if not response.results:
            return ""

        # Build context with length limit
        context_parts = []
        total_length = 0

        for result in response.results:
            item_text = f"## {result.item.title}\n{result.snippet or result.item.content[:500]}\n"

            if total_length + len(item_text) > max_length:
                break

            context_parts.append(item_text)
            total_length += len(item_text)

        if not context_parts:
            return ""

        return "# معلومات ذات صلة:\n\n" + "\n".join(context_parts)

    def search(
        self,
        query: str,
        source_types: Optional[List[SourceType]] = None,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Search the knowledge base.

        Args:
            query: Search query
            source_types: Filter by source types
            max_results: Maximum results

        Returns:
            List of search results
        """
        if not self._ready or not self._searcher:
            return []

        return self._searcher.search(
            query,
            SearchOptions(
                max_results=max_results,
                source_types=source_types
            )
        )

    def suggest(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions."""
        if not self._ready or not self._searcher:
            return []
        return self._searcher.suggest(partial_query, limit)

    def get_related(self, item_id: str, limit: int = 5) -> List[SearchResult]:
        """Get related items."""
        if not self._ready or not self._searcher:
            return []
        return self._searcher.get_related(item_id, limit)

    def get_stats(self) -> IndexStats:
        """Get index statistics."""
        if not self._indexer:
            return IndexStats()
        return self._indexer.get_stats()

    def get_all_items(self) -> List[KnowledgeItem]:
        """Get all indexed items."""
        if not self._indexer:
            return []
        return self._indexer.get_all_items()

    def _build_context(self, results: List[SearchResult]) -> str:
        """Build context text from search results."""
        context_parts = []

        for result in results:
            part = f"### {result.item.title}\n"
            part += f"المصدر: {result.item.source_type.value}\n"
            part += f"الدرجة: {result.score:.2f}\n\n"
            part += result.snippet or result.item.content[:300]
            part += "\n"
            context_parts.append(part)

        return "\n---\n".join(context_parts)


# Singleton instance
_engine: Optional[KnowledgeEngine] = None


def get_knowledge_engine() -> KnowledgeEngine:
    """Get the singleton knowledge engine instance."""
    global _engine
    if _engine is None:
        _engine = KnowledgeEngine()
    return _engine


def initialize_knowledge() -> bool:
    """Initialize the knowledge engine (convenience function)."""
    return get_knowledge_engine().initialize()


def query_knowledge(query: str) -> KnowledgeResponse:
    """Query the knowledge base (convenience function)."""
    engine = get_knowledge_engine()
    if not engine.is_ready():
        engine.initialize()
    return engine.query(query)


def get_ai_context(query: str) -> str:
    """Get AI context for a query (convenience function)."""
    engine = get_knowledge_engine()
    if not engine.is_ready():
        engine.initialize()
    return engine.get_context_for_prompt(query)
