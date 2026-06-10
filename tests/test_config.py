"""
配置模块单元测试
"""

import pytest
from pathlib import Path
from backend.app.config.settings import (
    Settings,
    LLMConfig,
    EmbeddingConfig,
    RAGConfig,
    load_settings_from_yaml,
)


class TestLLMConfig:
    """LLM 配置测试"""

    def test_default_values(self):
        """测试默认值"""
        config = LLMConfig()
        assert config.provider == "deepseek"
        assert config.model_name == "deepseek-chat"
        assert config.temperature == 0.7

    def test_custom_values(self):
        """测试自定义值"""
        config = LLMConfig(
            provider="openai",
            api_key="test-key",
            model_name="gpt-4o",
            temperature=0.5,
        )
        assert config.provider == "openai"
        assert config.api_key == "test-key"
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.5


class TestEmbeddingConfig:
    """Embedding 配置测试"""

    def test_default_values(self):
        """测试默认值"""
        config = EmbeddingConfig()
        assert config.provider == "local"
        assert config.model_name == "BAAI/bge-small-zh-v1.5"


class TestRAGConfig:
    """RAG 配置测试"""

    def test_default_values(self):
        """测试默认值"""
        config = RAGConfig()
        assert config.top_k == 5
        assert config.hybrid_weights == [0.6, 0.4]


class TestSettings:
    """Settings 测试"""

    def test_init(self):
        """测试初始化"""
        settings = Settings()
        assert settings.llm is not None
        assert settings.embedding is not None
        assert settings.rag is not None

    def test_setup_directories(self, temp_dir):
        """测试目录创建"""
        settings = Settings()
        settings.data_dir = temp_dir / "test_data"
        settings.setup_directories()

        assert settings.data_dir.exists()
        assert settings.chroma_db_dir.exists()
        assert settings.sqlite_dir.exists()
        assert settings.logs_dir.exists()
        assert settings.knowledge_base_dir.exists()


class TestLoadSettings:
    """配置加载测试"""

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        settings = load_settings_from_yaml("/nonexistent/path.yaml")
        assert settings is not None
        assert settings.llm.provider == "deepseek"  # 默认值
