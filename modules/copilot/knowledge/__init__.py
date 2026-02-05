"""
Knowledge Engine
================
Indexes and searches application knowledge for AI context.
"""

from .engine import KnowledgeEngine, get_knowledge_engine
from .indexer import KnowledgeIndexer
from .searcher import KnowledgeSearcher
from .sources import KnowledgeSource, DocumentSource, DatabaseSource, ModuleSource

__all__ = [
    "KnowledgeEngine",
    "get_knowledge_engine",
    "KnowledgeIndexer",
    "KnowledgeSearcher",
    "KnowledgeSource",
    "DocumentSource",
    "DatabaseSource",
    "ModuleSource"
]
