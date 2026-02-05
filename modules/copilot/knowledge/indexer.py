"""
Knowledge Indexer
=================
Indexes knowledge from various sources for fast retrieval.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import hashlib
import threading

from core.logging import app_logger
from .sources import (
    KnowledgeSource, KnowledgeItem, SourceType,
    DocumentSource, DatabaseSource, ModuleSource, HelpSource
)


@dataclass
class IndexStats:
    """Statistics about the knowledge index."""
    total_items: int = 0
    items_by_type: Dict[str, int] = field(default_factory=dict)
    last_indexed: Optional[datetime] = None
    index_duration_ms: float = 0.0


class KnowledgeIndexer:
    """
    Indexes knowledge from multiple sources.

    Features:
    - Multiple source support (docs, database, modules, help)
    - Incremental indexing
    - Text-based search preparation
    - Index persistence

    Usage:
        indexer = KnowledgeIndexer()
        indexer.add_source(DocumentSource("docs", "Documentation", "./docs"))
        indexer.index_all()

        items = indexer.get_all_items()
    """

    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize the indexer.

        Args:
            index_path: Path to store the index (optional)
        """
        self._sources: Dict[str, KnowledgeSource] = {}
        self._items: Dict[str, KnowledgeItem] = {}
        self._index_path = index_path or self._get_default_index_path()
        self._lock = threading.RLock()
        self._stats = IndexStats()

        # Load existing index if available
        self._load_index()

    def _get_default_index_path(self) -> str:
        """Get default index storage path."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        index_dir = os.path.join(base_dir, "data", "copilot")
        os.makedirs(index_dir, exist_ok=True)
        return os.path.join(index_dir, "knowledge_index.json")

    def add_source(self, source: KnowledgeSource) -> None:
        """
        Add a knowledge source.

        Args:
            source: The knowledge source to add
        """
        with self._lock:
            self._sources[source.source_id] = source
            app_logger.debug(f"Added knowledge source: {source.name}")

    def remove_source(self, source_id: str) -> bool:
        """
        Remove a knowledge source.

        Args:
            source_id: ID of the source to remove

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if source_id in self._sources:
                del self._sources[source_id]
                # Remove items from this source
                items_to_remove = [
                    item_id for item_id, item in self._items.items()
                    if item.metadata.get("source_id") == source_id
                ]
                for item_id in items_to_remove:
                    del self._items[item_id]
                return True
            return False

    def index_all(self) -> IndexStats:
        """
        Index all knowledge sources.

        Returns:
            Index statistics
        """
        import time
        start_time = time.time()

        with self._lock:
            self._items.clear()
            items_by_type: Dict[str, int] = {}

            for source_id, source in self._sources.items():
                if not source.enabled:
                    continue

                try:
                    items = source.extract()
                    for item in items:
                        # Add source_id to metadata
                        item.metadata["source_id"] = source_id
                        self._items[item.id] = item

                        # Update type counts
                        type_name = item.source_type.value
                        items_by_type[type_name] = items_by_type.get(type_name, 0) + 1

                    app_logger.info(f"Indexed {len(items)} items from {source.name}")

                except Exception as e:
                    app_logger.error(f"Error indexing source {source.name}: {e}")

            # Update stats
            duration = (time.time() - start_time) * 1000
            self._stats = IndexStats(
                total_items=len(self._items),
                items_by_type=items_by_type,
                last_indexed=datetime.now(),
                index_duration_ms=duration
            )

            # Save index
            self._save_index()

            app_logger.info(f"Knowledge indexing complete: {self._stats.total_items} items in {duration:.0f}ms")

        return self._stats

    def index_source(self, source_id: str) -> int:
        """
        Index a specific source.

        Args:
            source_id: ID of the source to index

        Returns:
            Number of items indexed
        """
        with self._lock:
            source = self._sources.get(source_id)
            if not source or not source.enabled:
                return 0

            try:
                # Remove old items from this source
                items_to_remove = [
                    item_id for item_id, item in self._items.items()
                    if item.metadata.get("source_id") == source_id
                ]
                for item_id in items_to_remove:
                    del self._items[item_id]

                # Index new items
                items = source.extract()
                for item in items:
                    item.metadata["source_id"] = source_id
                    self._items[item.id] = item

                self._save_index()
                return len(items)

            except Exception as e:
                app_logger.error(f"Error indexing source {source_id}: {e}")
                return 0

    def get_all_items(self) -> List[KnowledgeItem]:
        """Get all indexed items."""
        with self._lock:
            return list(self._items.values())

    def get_items_by_type(self, source_type: SourceType) -> List[KnowledgeItem]:
        """Get items by source type."""
        with self._lock:
            return [
                item for item in self._items.values()
                if item.source_type == source_type
            ]

    def get_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get a specific item by ID."""
        with self._lock:
            return self._items.get(item_id)

    def get_stats(self) -> IndexStats:
        """Get index statistics."""
        return self._stats

    def _save_index(self) -> None:
        """Save index to disk."""
        try:
            data = {
                "version": 1,
                "stats": {
                    "total_items": self._stats.total_items,
                    "items_by_type": self._stats.items_by_type,
                    "last_indexed": self._stats.last_indexed.isoformat() if self._stats.last_indexed else None,
                    "index_duration_ms": self._stats.index_duration_ms
                },
                "items": [item.to_dict() for item in self._items.values()]
            }

            with open(self._index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            app_logger.error(f"Error saving knowledge index: {e}")

    def _load_index(self) -> None:
        """Load index from disk."""
        if not os.path.exists(self._index_path):
            return

        try:
            with open(self._index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get("version") != 1:
                return

            # Load stats
            stats_data = data.get("stats", {})
            self._stats = IndexStats(
                total_items=stats_data.get("total_items", 0),
                items_by_type=stats_data.get("items_by_type", {}),
                last_indexed=datetime.fromisoformat(stats_data["last_indexed"]) if stats_data.get("last_indexed") else None,
                index_duration_ms=stats_data.get("index_duration_ms", 0.0)
            )

            # Load items
            for item_data in data.get("items", []):
                item = KnowledgeItem.from_dict(item_data)
                self._items[item.id] = item

            app_logger.debug(f"Loaded {len(self._items)} items from knowledge index")

        except Exception as e:
            app_logger.error(f"Error loading knowledge index: {e}")

    def clear(self) -> None:
        """Clear the index."""
        with self._lock:
            self._items.clear()
            self._stats = IndexStats()

            if os.path.exists(self._index_path):
                os.remove(self._index_path)


def create_default_indexer() -> KnowledgeIndexer:
    """Create an indexer with default sources."""
    indexer = KnowledgeIndexer()

    # Add default sources
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    # Documentation source
    docs_path = os.path.join(base_dir, "claude")
    if os.path.exists(docs_path):
        indexer.add_source(DocumentSource("docs", "Documentation", docs_path))

    # Database schema source
    indexer.add_source(DatabaseSource("db_schema", "Database Schema"))

    # Module info source
    indexer.add_source(ModuleSource("modules", "Application Modules"))

    # Help content source
    indexer.add_source(HelpSource("help", "Help Content"))

    return indexer
