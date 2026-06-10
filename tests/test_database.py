"""
数据库模块单元测试
"""

import pytest
import tempfile
from pathlib import Path
from backend.app.models.database import Database


@pytest.fixture
def test_db():
    """创建测试数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database()
        db._conn = None  # 重置连接

        # 使用临时数据库
        import sqlite3
        db._conn = sqlite3.connect(str(db_path))
        db._conn.row_factory = sqlite3.Row
        db._init_tables()

        yield db

        db.close()


class TestDatabase:
    """数据库测试"""

    def test_init_tables(self, test_db):
        """测试表创建"""
        cursor = test_db._conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "sessions" in tables
        assert "messages" in tables
        assert "documents" in tables

    def test_create_session(self, test_db):
        """测试创建会话"""
        session_id = test_db.create_session("test-session-1")
        assert session_id == "test-session-1"

        # 检查会话是否创建成功
        sessions = test_db.get_sessions()
        assert len(sessions) >= 1

    def test_add_message(self, test_db):
        """测试添加消息"""
        test_db.create_session("test-session-2")

        msg_id = test_db.add_message(
            session_id="test-session-2",
            role="user",
            content="你好",
        )
        assert msg_id is not None

        # 检查消息是否添加成功
        messages = test_db.get_messages("test-session-2")
        assert len(messages) >= 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好"

    def test_add_message_with_sources(self, test_db):
        """测试添加带引用的消息"""
        test_db.create_session("test-session-3")

        msg_id = test_db.add_message(
            session_id="test-session-3",
            role="assistant",
            content="这是回答",
            sources=["doc1.pdf", "doc2.txt"],
        )
        assert msg_id is not None

        messages = test_db.get_messages("test-session-3")
        assert len(messages) >= 1
        assert messages[0]["sources"] == ["doc1.pdf", "doc2.txt"]

    def test_clear_messages(self, test_db):
        """测试清空消息"""
        test_db.create_session("test-session-4")
        test_db.add_message("test-session-4", "user", "消息1")
        test_db.add_message("test-session-4", "user", "消息2")

        count = test_db.clear_messages("test-session-4")
        assert count == 2

        messages = test_db.get_messages("test-session-4")
        assert len(messages) == 0

    def test_document_operations(self, test_db):
        """测试文档操作"""
        # 添加文档
        test_db.add_document(
            doc_id="doc-1",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            file_hash="abc123",
            chunk_count=10,
        )

        # 获取文档列表
        docs = test_db.get_documents()
        assert len(docs) >= 1
        assert docs[0]["filename"] == "test.pdf"

        # 获取单个文档
        doc = test_db.get_document("doc-1")
        assert doc is not None
        assert doc["filename"] == "test.pdf"

        # 删除文档
        result = test_db.delete_document("doc-1")
        assert result is True

    def test_stats(self, test_db):
        """测试统计功能"""
        test_db.create_session("test-session-5")
        test_db.add_message("test-session-5", "user", "消息")

        stats = test_db.get_stats()
        assert "sessions" in stats
        assert "messages" in stats
        assert stats["sessions"] >= 1
        assert stats["messages"] >= 1
