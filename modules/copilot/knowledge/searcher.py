"""
Knowledge Searcher
==================
Searches indexed knowledge for relevant information.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import threading

from core.logging import app_logger
from .sources import KnowledgeItem, SourceType


@dataclass
class SearchResult:
    """A search result with relevance score."""
    item: KnowledgeItem
    score: float
    matched_keywords: List[str] = field(default_factory=list)
    snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.item.id,
            "title": self.item.title,
            "content": self.snippet or self.item.content[:200],
            "score": self.score,
            "source_type": self.item.source_type.value,
            "matched_keywords": self.matched_keywords
        }


@dataclass
class SearchOptions:
    """Options for search queries."""
    max_results: int = 10
    min_score: float = 0.1
    source_types: Optional[List[SourceType]] = None
    boost_recent: bool = True
    include_snippets: bool = True


class KnowledgeSearcher:
    """
    Searches the knowledge index.

    Features:
    - Keyword-based search
    - Relevance scoring
    - Source type filtering
    - Snippet extraction
    - Arabic and English support

    Usage:
        searcher = KnowledgeSearcher(items)
        results = searcher.search("موظفين")
    """

    # Common Arabic stop words to ignore
    ARABIC_STOP_WORDS = {
        "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي",
        "هو", "هي", "أو", "و", "لا", "ما", "كل", "بعض", "كان", "كانت",
        "يكون", "تكون", "أن", "إن", "لم", "لن", "قد", "كما", "حتى", "إذا"
    }

    # Common English stop words
    ENGLISH_STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "or", "and", "not", "this", "that"
    }

    def __init__(self, items: Optional[List[KnowledgeItem]] = None):
        """
        Initialize the searcher.

        Args:
            items: List of knowledge items to search
        """
        self._items: List[KnowledgeItem] = items or []
        self._lock = threading.RLock()

        # Build inverted index for faster search
        self._inverted_index: Dict[str, List[Tuple[str, float]]] = {}
        self._rebuild_index()

    def set_items(self, items: List[KnowledgeItem]) -> None:
        """Set the items to search."""
        with self._lock:
            self._items = items
            self._rebuild_index()

    def add_item(self, item: KnowledgeItem) -> None:
        """Add an item to the search index."""
        with self._lock:
            self._items.append(item)
            self._index_item(item)

    def _rebuild_index(self) -> None:
        """Rebuild the inverted index."""
        self._inverted_index.clear()
        for item in self._items:
            self._index_item(item)

    def _index_item(self, item: KnowledgeItem) -> None:
        """Add an item to the inverted index."""
        # Extract and weight terms
        terms_with_weights = []

        # Title terms (weight: 3.0)
        title_terms = self._tokenize(item.title)
        terms_with_weights.extend((term, 3.0) for term in title_terms)

        # Keyword terms (weight: 2.5)
        for keyword in item.keywords:
            kw_terms = self._tokenize(keyword)
            terms_with_weights.extend((term, 2.5) for term in kw_terms)

        # Content terms (weight: 1.0)
        content_terms = self._tokenize(item.content)
        terms_with_weights.extend((term, 1.0) for term in content_terms)

        # Add to inverted index
        for term, weight in terms_with_weights:
            if term not in self._inverted_index:
                self._inverted_index[term] = []
            self._inverted_index[term].append((item.id, weight))

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable terms."""
        if not text:
            return []

        # Convert to lowercase
        text = text.lower()

        # Split on non-alphanumeric characters (preserving Arabic)
        tokens = re.findall(r'[\u0600-\u06FF]+|[a-z0-9]+', text)

        # Remove stop words
        tokens = [
            t for t in tokens
            if t not in self.ARABIC_STOP_WORDS and t not in self.ENGLISH_STOP_WORDS
            and len(t) > 1
        ]

        return tokens

    def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """
        Search for relevant knowledge items.

        Args:
            query: The search query
            options: Search options

        Returns:
            List of search results sorted by relevance
        """
        if not query or not query.strip():
            return []

        options = options or SearchOptions()

        with self._lock:
            # Tokenize query
            query_terms = self._tokenize(query)

            if not query_terms:
                return []

            # Calculate scores for each item
            scores: Dict[str, Dict[str, Any]] = {}

            for term in query_terms:
                # Find exact matches
                if term in self._inverted_index:
                    for item_id, weight in self._inverted_index[term]:
                        if item_id not in scores:
                            scores[item_id] = {"score": 0.0, "matched": []}
                        scores[item_id]["score"] += weight
                        if term not in scores[item_id]["matched"]:
                            scores[item_id]["matched"].append(term)

                # Find partial matches (prefix)
                for indexed_term, items in self._inverted_index.items():
                    if indexed_term.startswith(term) and indexed_term != term:
                        for item_id, weight in items:
                            if item_id not in scores:
                                scores[item_id] = {"score": 0.0, "matched": []}
                            scores[item_id]["score"] += weight * 0.5  # Partial match penalty
                            if term not in scores[item_id]["matched"]:
                                scores[item_id]["matched"].append(term)

            # Build results
            results = []
            items_dict = {item.id: item for item in self._items}

            for item_id, score_data in scores.items():
                item = items_dict.get(item_id)
                if not item:
                    continue

                score = score_data["score"]

                # Apply source type filter
                if options.source_types and item.source_type not in options.source_types:
                    continue

                # Normalize score
                score = min(score / (len(query_terms) * 3.0), 1.0)

                # Apply minimum score filter
                if score < options.min_score:
                    continue

                # Boost recent items
                if options.boost_recent and item.indexed_at:
                    days_old = (datetime.now() - item.indexed_at).days
                    if days_old < 7:
                        score *= 1.1

                # Extract snippet
                snippet = ""
                if options.include_snippets:
                    snippet = self._extract_snippet(item.content, query_terms)

                results.append(SearchResult(
                    item=item,
                    score=score,
                    matched_keywords=score_data["matched"],
                    snippet=snippet
                ))

            # Sort by score (descending)
            results.sort(key=lambda r: r.score, reverse=True)

            # Limit results
            return results[:options.max_results]

    def _extract_snippet(self, content: str, terms: List[str], context_size: int = 100) -> str:
        """Extract a relevant snippet from content."""
        if not content:
            return ""

        content_lower = content.lower()

        # Find the first occurrence of any search term
        best_pos = -1
        for term in terms:
            pos = content_lower.find(term)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos

        if best_pos == -1:
            # No term found, return beginning
            return content[:context_size * 2] + "..."

        # Extract context around the match
        start = max(0, best_pos - context_size)
        end = min(len(content), best_pos + context_size)

        snippet = content[start:end]

        # Clean up snippet
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet.strip()

    def suggest(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Suggest completions for a partial query.

        Args:
            partial_query: The partial query
            limit: Maximum number of suggestions

        Returns:
            List of suggested terms
        """
        if not partial_query or len(partial_query) < 2:
            return []

        partial = partial_query.lower()
        suggestions = []

        with self._lock:
            # Find terms that start with the partial query
            for term in self._inverted_index.keys():
                if term.startswith(partial) and term != partial:
                    suggestions.append(term)
                    if len(suggestions) >= limit:
                        break

        return suggestions

    def get_related(self, item_id: str, limit: int = 5) -> List[SearchResult]:
        """
        Get items related to a specific item.

        Args:
            item_id: ID of the source item
            limit: Maximum number of related items

        Returns:
            List of related items
        """
        with self._lock:
            # Find the source item
            source_item = None
            for item in self._items:
                if item.id == item_id:
                    source_item = item
                    break

            if not source_item:
                return []

            # Use keywords and title as search query
            query = source_item.title + " " + " ".join(source_item.keywords)

            # Search and exclude the source item
            results = self.search(query, SearchOptions(max_results=limit + 1))
            return [r for r in results if r.item.id != item_id][:limit]
