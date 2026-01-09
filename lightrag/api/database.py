import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("lightrag.db")

class DatabaseManager:
    def __init__(self, db_path: str = "chat.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, user_id)
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id, user_id) REFERENCES conversations (id, user_id)
                )
            """)

            # Cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            conn.commit()

    def get_or_create_conversation(self, user_id: str, session_id: str):
        """Ensure a conversation exists for the user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM conversations WHERE id = ? AND user_id = ?", 
                (session_id, user_id)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO conversations (id, user_id) VALUES (?, ?)",
                    (session_id, user_id)
                )
                conn.commit()
                return True
            return False

    def add_message(self, conversation_id: str, user_id: str, role: str, content: str):
        """Add a message to history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (conversation_id, user_id, role, content)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, user_id, role, content)
            )
            conn.commit()

    def get_history(self, conversation_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content 
                FROM messages 
                WHERE conversation_id = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (conversation_id, user_id, limit)
            )
            rows = cursor.fetchall()
            # Return in chronological order (oldest first) for LLM context
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def _hash_query(self, query_text: str) -> str:
        """Create a consistent hash for a query string"""
        return hashlib.sha256(query_text.strip().lower().encode()).hexdigest()

    def get_cached_response(self, query_text: str) -> Optional[str]:
        """Get cached response if exists"""
        query_hash = self._hash_query(query_text)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response FROM response_cache WHERE query_hash = ?",
                (query_hash,)
            )
            row = cursor.fetchone()
            if row:
                # Update access stats
                cursor.execute(
                    "UPDATE response_cache SET access_count = access_count + 1 WHERE query_hash = ?",
                    (query_hash,)
                )
                conn.commit()
                return row[0]
            return None

    def cache_response(self, query_text: str, response: str):
        """Save response to cache"""
        query_hash = self._hash_query(query_text)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO response_cache (query_hash, query_text, response)
                VALUES (?, ?, ?)
                """,
                (query_hash, query_text, response)
            )
            conn.commit()
