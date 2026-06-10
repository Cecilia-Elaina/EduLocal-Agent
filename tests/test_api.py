"""
API 模块单元测试
"""

import pytest


class TestImports:
    """导入测试"""

    def test_import_main(self):
        """测试导入主模块"""
        from backend.main import app
        assert app is not None

    def test_import_chat_api(self):
        """测试导入 Chat API"""
        from backend.app.api.chat import router
        assert router is not None

    def test_import_documents_api(self):
        """测试导入 Documents API"""
        from backend.app.api.documents import router
        assert router is not None

    def test_import_settings_api(self):
        """测试导入 Settings API"""
        from backend.app.api.settings import router
        assert router is not None


class TestModels:
    """模型测试"""

    def test_import_llm_factory(self):
        """测试导入 LLM Factory"""
        from backend.app.models.llm import LLMFactory
        assert LLMFactory is not None

    def test_import_embeddings_factory(self):
        """测试导入 Embeddings Factory"""
        from backend.app.models.embeddings import EmbeddingFactory
        assert EmbeddingFactory is not None

    def test_import_database(self):
        """测试导入 Database"""
        from backend.app.models.database import Database
        assert Database is not None
