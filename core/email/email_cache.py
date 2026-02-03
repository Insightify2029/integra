"""
Email Cache
===========
SQLite-based cache for offline email access.
"""

from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import sqlite3
import os
import threading
from pathlib import Path

from .email_models import Email, EmailImportance
from core.logging import app_logger


class EmailCache:
    """
    SQLite cache for emails.

    Features:
    - Offline email access
    - Fast search
    - AI analysis storage
    - Automatic cleanup of old emails

    Usage:
        cache = EmailCache()
        cache.save_emails(emails)
        results = cache.search("موضوع البحث")
    """

    _instance: Optional['EmailCache'] = None
    _lock = threading.Lock()

    # Default cache settings
    DEFAULT_DB_PATH = "data/email_cache.db"
    MAX_CACHE_DAYS = 30  # Keep emails for 30 days

    def __new__(cls, db_path: Optional[str] = None):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return

        self._db_path = db_path or self.DEFAULT_DB_PATH
        self._ensure_directory()
        self._init_database()
        self._initialized = True

    def _ensure_directory(self):
        """Ensure the data directory exists."""
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Emails table
                CREATE TABLE IF NOT EXISTS emails (
                    entry_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    subject TEXT,
                    body TEXT,
                    body_html TEXT,
                    sender_name TEXT,
                    sender_email TEXT,
                    recipients_to TEXT,
                    recipients_cc TEXT,
                    received_time TEXT,
                    sent_time TEXT,
                    is_read INTEGER DEFAULT 0,
                    is_flagged INTEGER DEFAULT 0,
                    importance INTEGER DEFAULT 1,
                    has_attachments INTEGER DEFAULT 0,
                    folder_name TEXT,
                    folder_id TEXT,
                    categories TEXT,
                    -- AI fields
                    ai_summary TEXT,
                    ai_category TEXT,
                    ai_priority TEXT,
                    ai_tasks TEXT,
                    ai_analyzed_at TEXT,
                    -- Cache metadata
                    cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                -- Attachments table
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_entry_id TEXT,
                    filename TEXT,
                    size INTEGER,
                    content_type TEXT,
                    local_path TEXT,
                    FOREIGN KEY (email_entry_id) REFERENCES emails(entry_id)
                );

                -- Folders table
                CREATE TABLE IF NOT EXISTS folders (
                    entry_id TEXT PRIMARY KEY,
                    name TEXT,
                    folder_type INTEGER,
                    unread_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0,
                    last_sync TEXT
                );

                -- Search index
                CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject);
                CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);
                CREATE INDEX IF NOT EXISTS idx_emails_received ON emails(received_time);
                CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder_name);
                CREATE INDEX IF NOT EXISTS idx_emails_unread ON emails(is_read);

                -- Full-text search
                CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
                    entry_id,
                    subject,
                    body,
                    sender_name,
                    sender_email,
                    content='emails',
                    content_rowid='rowid'
                );

                -- Triggers for FTS sync
                CREATE TRIGGER IF NOT EXISTS emails_ai AFTER INSERT ON emails BEGIN
                    INSERT INTO emails_fts(entry_id, subject, body, sender_name, sender_email)
                    VALUES (new.entry_id, new.subject, new.body, new.sender_name, new.sender_email);
                END;

                CREATE TRIGGER IF NOT EXISTS emails_ad AFTER DELETE ON emails BEGIN
                    INSERT INTO emails_fts(emails_fts, entry_id, subject, body, sender_name, sender_email)
                    VALUES ('delete', old.entry_id, old.subject, old.body, old.sender_name, old.sender_email);
                END;

                CREATE TRIGGER IF NOT EXISTS emails_au AFTER UPDATE ON emails BEGIN
                    INSERT INTO emails_fts(emails_fts, entry_id, subject, body, sender_name, sender_email)
                    VALUES ('delete', old.entry_id, old.subject, old.body, old.sender_name, old.sender_email);
                    INSERT INTO emails_fts(entry_id, subject, body, sender_name, sender_email)
                    VALUES (new.entry_id, new.subject, new.body, new.sender_name, new.sender_email);
                END;
            """)
            conn.commit()
            app_logger.debug("Email cache database initialized")

    def save_email(self, email: Email) -> bool:
        """Save a single email to cache."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO emails (
                        entry_id, conversation_id, subject, body, body_html,
                        sender_name, sender_email, recipients_to, recipients_cc,
                        received_time, sent_time, is_read, is_flagged,
                        importance, has_attachments, folder_name, folder_id,
                        categories, ai_summary, ai_category, ai_priority,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    email.entry_id,
                    email.conversation_id,
                    email.subject,
                    email.body,
                    email.body_html,
                    email.sender_name,
                    email.sender_email,
                    ','.join(email.to),
                    ','.join(email.cc),
                    email.received_time.isoformat() if email.received_time else None,
                    email.sent_time.isoformat() if email.sent_time else None,
                    1 if email.is_read else 0,
                    1 if email.is_flagged else 0,
                    email.importance.value,
                    1 if email.has_attachments else 0,
                    email.folder_name,
                    email.folder_id,
                    ','.join(email.categories),
                    email.ai_summary,
                    email.ai_category,
                    email.ai_priority
                ))

                # Save attachments
                if email.attachments:
                    conn.execute("DELETE FROM attachments WHERE email_entry_id = ?", (email.entry_id,))
                    for att in email.attachments:
                        conn.execute("""
                            INSERT INTO attachments (email_entry_id, filename, size, content_type, local_path)
                            VALUES (?, ?, ?, ?, ?)
                        """, (email.entry_id, att.filename, att.size, att.content_type, att.path))

                conn.commit()
                return True

        except Exception as e:
            app_logger.error(f"Failed to save email to cache: {e}")
            return False

    def save_emails(self, emails: List[Email]) -> int:
        """
        Save multiple emails to cache.

        Returns:
            Number of emails saved
        """
        saved = 0
        for email in emails:
            if self.save_email(email):
                saved += 1
        return saved

    def get_email(self, entry_id: str) -> Optional[Email]:
        """Get a single email by ID."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM emails WHERE entry_id = ?",
                    (entry_id,)
                ).fetchone()

                if row:
                    return self._row_to_email(row)

        except Exception as e:
            app_logger.error(f"Failed to get email from cache: {e}")

        return None

    def get_emails(
        self,
        folder_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        flagged_only: bool = False
    ) -> List[Email]:
        """Get emails from cache with filters."""
        emails = []

        try:
            query = "SELECT * FROM emails WHERE 1=1"
            params = []

            if folder_name:
                query += " AND folder_name = ?"
                params.append(folder_name)

            if unread_only:
                query += " AND is_read = 0"

            if flagged_only:
                query += " AND is_flagged = 1"

            query += " ORDER BY received_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            with self._get_connection() as conn:
                rows = conn.execute(query, params).fetchall()
                emails = [self._row_to_email(row) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get emails from cache: {e}")

        return emails

    def search(
        self,
        query: str,
        limit: int = 50,
        folder_name: Optional[str] = None
    ) -> List[Email]:
        """
        Full-text search in cached emails.

        Args:
            query: Search query
            limit: Maximum results
            folder_name: Filter by folder

        Returns:
            List of matching emails
        """
        emails = []

        try:
            sql = """
                SELECT e.* FROM emails e
                JOIN emails_fts fts ON e.entry_id = fts.entry_id
                WHERE emails_fts MATCH ?
            """
            params = [query]

            if folder_name:
                sql += " AND e.folder_name = ?"
                params.append(folder_name)

            sql += " ORDER BY e.received_time DESC LIMIT ?"
            params.append(limit)

            with self._get_connection() as conn:
                rows = conn.execute(sql, params).fetchall()
                emails = [self._row_to_email(row) for row in rows]

        except Exception as e:
            app_logger.error(f"Search failed: {e}")
            # Fallback to LIKE search
            return self._search_like(query, limit, folder_name)

        return emails

    def _search_like(
        self,
        query: str,
        limit: int,
        folder_name: Optional[str]
    ) -> List[Email]:
        """Fallback LIKE search."""
        emails = []
        try:
            sql = """
                SELECT * FROM emails
                WHERE (subject LIKE ? OR body LIKE ? OR sender_name LIKE ? OR sender_email LIKE ?)
            """
            search_pattern = f"%{query}%"
            params = [search_pattern] * 4

            if folder_name:
                sql += " AND folder_name = ?"
                params.append(folder_name)

            sql += " ORDER BY received_time DESC LIMIT ?"
            params.append(limit)

            with self._get_connection() as conn:
                rows = conn.execute(sql, params).fetchall()
                emails = [self._row_to_email(row) for row in rows]

        except Exception as e:
            app_logger.error(f"LIKE search failed: {e}")

        return emails

    def _row_to_email(self, row: sqlite3.Row) -> Email:
        """Convert database row to Email object."""
        return Email(
            entry_id=row['entry_id'],
            conversation_id=row['conversation_id'],
            subject=row['subject'] or "",
            body=row['body'] or "",
            body_html=row['body_html'],
            sender_name=row['sender_name'] or "",
            sender_email=row['sender_email'] or "",
            to=row['recipients_to'].split(',') if row['recipients_to'] else [],
            cc=row['recipients_cc'].split(',') if row['recipients_cc'] else [],
            received_time=datetime.fromisoformat(row['received_time']) if row['received_time'] else None,
            sent_time=datetime.fromisoformat(row['sent_time']) if row['sent_time'] else None,
            is_read=bool(row['is_read']),
            is_flagged=bool(row['is_flagged']),
            importance=EmailImportance(row['importance']),
            has_attachments=bool(row['has_attachments']),
            folder_name=row['folder_name'],
            folder_id=row['folder_id'],
            categories=row['categories'].split(',') if row['categories'] else [],
            ai_summary=row['ai_summary'],
            ai_category=row['ai_category'],
            ai_priority=row['ai_priority']
        )

    def update_ai_analysis(
        self,
        entry_id: str,
        summary: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        tasks: Optional[List[str]] = None
    ) -> bool:
        """Update AI analysis for an email."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE emails SET
                        ai_summary = COALESCE(?, ai_summary),
                        ai_category = COALESCE(?, ai_category),
                        ai_priority = COALESCE(?, ai_priority),
                        ai_tasks = COALESCE(?, ai_tasks),
                        ai_analyzed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE entry_id = ?
                """, (
                    summary, category, priority,
                    ','.join(tasks) if tasks else None,
                    entry_id
                ))
                conn.commit()
                return True

        except Exception as e:
            app_logger.error(f"Failed to update AI analysis: {e}")
            return False

    def get_unanalyzed_emails(self, limit: int = 10) -> List[Email]:
        """Get emails that haven't been analyzed by AI."""
        emails = []
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM emails
                    WHERE ai_analyzed_at IS NULL
                    ORDER BY received_time DESC
                    LIMIT ?
                """, (limit,)).fetchall()
                emails = [self._row_to_email(row) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get unanalyzed emails: {e}")

        return emails

    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            with self._get_connection() as conn:
                total = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
                unread = conn.execute("SELECT COUNT(*) FROM emails WHERE is_read = 0").fetchone()[0]
                flagged = conn.execute("SELECT COUNT(*) FROM emails WHERE is_flagged = 1").fetchone()[0]
                analyzed = conn.execute("SELECT COUNT(*) FROM emails WHERE ai_analyzed_at IS NOT NULL").fetchone()[0]

                return {
                    'total': total,
                    'unread': unread,
                    'flagged': flagged,
                    'analyzed': analyzed,
                    'unanalyzed': total - analyzed
                }

        except Exception as e:
            app_logger.error(f"Failed to get stats: {e}")
            return {}

    def cleanup_old_emails(self, days: int = None) -> int:
        """Remove emails older than specified days."""
        days = days or self.MAX_CACHE_DAYS
        cutoff = datetime.now() - timedelta(days=days)

        try:
            with self._get_connection() as conn:
                # Delete attachments first
                conn.execute("""
                    DELETE FROM attachments WHERE email_entry_id IN (
                        SELECT entry_id FROM emails WHERE cached_at < ?
                    )
                """, (cutoff.isoformat(),))

                # Delete emails
                cursor = conn.execute(
                    "DELETE FROM emails WHERE cached_at < ?",
                    (cutoff.isoformat(),)
                )
                deleted = cursor.rowcount
                conn.commit()

                app_logger.info(f"Cleaned up {deleted} old emails from cache")
                return deleted

        except Exception as e:
            app_logger.error(f"Cleanup failed: {e}")
            return 0

    def clear_all(self) -> bool:
        """Clear all cached data."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM attachments")
                conn.execute("DELETE FROM emails")
                conn.execute("DELETE FROM folders")
                conn.commit()
                return True

        except Exception as e:
            app_logger.error(f"Failed to clear cache: {e}")
            return False


# Singleton instance
_cache: Optional[EmailCache] = None


def get_email_cache() -> EmailCache:
    """Get the singleton email cache."""
    global _cache
    if _cache is None:
        _cache = EmailCache()
    return _cache


def cache_emails(emails: List[Email]) -> int:
    """Quick function to cache emails."""
    return get_email_cache().save_emails(emails)


def get_cached_emails(folder_name: Optional[str] = None, **kwargs) -> List[Email]:
    """Quick function to get cached emails."""
    return get_email_cache().get_emails(folder_name, **kwargs)


def search_cached_emails(query: str, **kwargs) -> List[Email]:
    """Quick function to search cached emails."""
    return get_email_cache().search(query, **kwargs)
