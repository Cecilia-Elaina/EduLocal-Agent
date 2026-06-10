"""
SQLite 数据库管理
存储会话历史、文档索引、学情数据
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from backend.app.config import get_settings


class Database:
    """SQLite 数据库管理器"""

    _instance: Optional['Database'] = None
    _conn: Optional[sqlite3.Connection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        """建立数据库连接"""
        if self._conn is not None:
            return

        settings = get_settings()
        db_path = settings.sqlite_dir / "edulocal.db"

        logger.info(f"连接数据库: {db_path}")

        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        self._init_tables()

    def _init_tables(self):
        """初始化数据库表"""
        cursor = self._conn.cursor()

        # 会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 对话消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # 文档索引表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 学情记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question TEXT NOT NULL,
                answer TEXT,
                knowledge_points TEXT,
                is_correct INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_session ON learning_records(session_id)")

        self._conn.commit()
        logger.info("数据库表初始化完成")

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("数据库连接已关闭")

    # ============ 会话管理 ============

    def create_session(self, session_id: str) -> str:
        """创建新会话"""
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO sessions (id) VALUES (?)",
            (session_id,)
        )
        self._conn.commit()
        return session_id

    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    # ============ 消息管理 ============

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[str]] = None,
    ) -> int:
        """添加消息"""
        import json

        cursor = self._conn.cursor()
        sources_json = json.dumps(sources) if sources else None

        cursor.execute(
            "INSERT INTO messages (session_id, role, content, sources) VALUES (?, ?, ?, ?)",
            (session_id, role, content, sources_json)
        )

        # 更新会话时间
        cursor.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )

        self._conn.commit()
        return cursor.lastrowid

    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取会话消息"""
        import json

        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit)
        )

        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            if msg['sources']:
                msg['sources'] = json.loads(msg['sources'])
            messages.append(msg)

        return messages

    def clear_messages(self, session_id: str) -> int:
        """清空会话消息"""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self._conn.commit()
        return cursor.rowcount

    # ============ 文档管理 ============

    def add_document(
        self,
        doc_id: str,
        filename: str,
        file_path: str,
        file_hash: str,
        chunk_count: int,
    ):
        """添加文档记录"""
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO documents (id, filename, file_path, file_hash, chunk_count) VALUES (?, ?, ?, ?, ?)",
            (doc_id, filename, file_path, file_hash, chunk_count)
        )
        self._conn.commit()

    def get_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    # ============ 学情记录 ============

    def add_learning_record(
        self,
        session_id: Optional[str],
        question: str,
        answer: Optional[str] = None,
        knowledge_points: Optional[List[str]] = None,
        is_correct: Optional[bool] = None,
    ):
        """添加学情记录"""
        import json

        cursor = self._conn.cursor()
        kp_json = json.dumps(knowledge_points) if knowledge_points else None

        cursor.execute(
            "INSERT INTO learning_records (session_id, question, answer, knowledge_points, is_correct) VALUES (?, ?, ?, ?, ?)",
            (session_id, question, answer, kp_json, 1 if is_correct else (0 if is_correct is not None else None))
        )
        self._conn.commit()

    def get_learning_records(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取学情记录"""
        import json

        cursor = self._conn.cursor()

        if session_id:
            cursor.execute(
                "SELECT * FROM learning_records WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM learning_records ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        records = []
        for row in cursor.fetchall():
            record = dict(row)
            if record['knowledge_points']:
                record['knowledge_points'] = json.loads(record['knowledge_points'])
            records.append(record)

        return records

    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计"""
        cursor = self._conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sessions")
        session_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents")
        document_count = cursor.fetchone()[0]

        return {
            "sessions": session_count,
            "messages": message_count,
            "documents": document_count,
        }


# 全局数据库实例
_db: Optional[Database] = None


def get_database() -> Database:
    """获取数据库实例"""
    global _db
    if _db is None:
        _db = Database()
        _db.connect()
    return _db
