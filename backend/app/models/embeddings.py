"""
Embedding 模型统一接口
支持本地 BGE-small 模型
"""

from typing import Optional
from langchain_core.embeddings import Embeddings
from loguru import logger

from backend.app.config import get_settings


class EmbeddingFactory:
    """Embedding 工厂类"""

    _instance: Optional[Embeddings] = None

    @classmethod
    def get_embeddings(cls, force_new: bool = False) -> Embeddings:
        """
        获取 Embedding 实例

        Args:
            force_new: 是否强制创建新实例

        Returns:
            Embeddings 实例
        """
        if not force_new and cls._instance:
            return cls._instance

        settings = get_settings()
        provider = settings.embedding.provider
        model_name = settings.embedding.model_name

        logger.info(f"创建 Embedding 实例: provider={provider}, model={model_name}")

        if provider == "local":
            cls._instance = cls._create_local(model_name)
        else:
            raise ValueError(f"不支持的 Embedding 提供商: {provider}")

        logger.info("Embedding 实例创建成功")
        return cls._instance

    @classmethod
    def _create_local(cls, model_name: str) -> Embeddings:
        """创建本地 Embedding（使用 sentence-transformers）"""
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    @classmethod
    def reset(cls):
        """重置实例"""
        cls._instance = None


def get_embeddings(force_new: bool = False) -> Embeddings:
    """便捷函数：获取 Embedding 实例"""
    return EmbeddingFactory.get_embeddings(force_new=force_new)
