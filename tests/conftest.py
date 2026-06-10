"""
测试配置和 fixtures
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "llm": {
            "provider": "deepseek",
            "api_key": "test-key",
            "model_name": "deepseek-chat",
            "temperature": 0.7,
        },
        "embedding": {
            "provider": "local",
            "model_name": "BAAI/bge-small-zh-v1.5",
        },
        "rag": {
            "top_k": 5,
            "hybrid_weights": [0.6, 0.4],
        },
    }
