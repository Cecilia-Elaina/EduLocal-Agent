"""
LLM 统一接口模块
支持 DeepSeek / OpenAI / Ollama 切换
"""

from typing import Optional
from langchain_core.language_models import BaseChatModel
from loguru import logger

from backend.app.config import get_settings


class LLMFactory:
    """LLM 工厂类 - 根据配置创建对应的 LLM 实例"""

    _instance: Optional[BaseChatModel] = None
    _current_provider: Optional[str] = None

    @classmethod
    def get_llm(cls, force_new: bool = False) -> BaseChatModel:
        """
        获取 LLM 实例（单例模式）

        Args:
            force_new: 是否强制创建新实例

        Returns:
            BaseChatModel 实例
        """
        settings = get_settings()
        provider = settings.llm.provider

        # 如果配置未变更且已有实例，直接返回
        if not force_new and cls._instance and cls._current_provider == provider:
            return cls._instance

        logger.info(f"创建 LLM 实例: provider={provider}")

        if provider == "deepseek":
            cls._instance = cls._create_deepseek(settings)
        elif provider == "openai":
            cls._instance = cls._create_openai(settings)
        elif provider == "ollama":
            cls._instance = cls._create_ollama(settings)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

        cls._current_provider = provider
        logger.info(f"LLM 实例创建成功: {provider}/{settings.llm.model_name}")

        return cls._instance

    @classmethod
    def _create_deepseek(cls, settings) -> BaseChatModel:
        """创建 DeepSeek LLM"""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm.model_name,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url or "https://api.deepseek.com",
            temperature=settings.llm.temperature,
        )

    @classmethod
    def _create_openai(cls, settings) -> BaseChatModel:
        """创建 OpenAI LLM"""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm.model_name,
            api_key=settings.llm.api_key,
            base_url=settings.llm.base_url,
            temperature=settings.llm.temperature,
        )

    @classmethod
    def _create_ollama(cls, settings) -> BaseChatModel:
        """创建 Ollama LLM"""
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.local_llm.model,
            base_url=settings.local_llm.ollama_url,
            temperature=settings.llm.temperature,
        )

    @classmethod
    def reset(cls):
        """重置实例（用于配置变更后重新创建）"""
        cls._instance = None
        cls._current_provider = None


def get_llm(force_new: bool = False) -> BaseChatModel:
    """便捷函数：获取 LLM 实例"""
    return LLMFactory.get_llm(force_new=force_new)
