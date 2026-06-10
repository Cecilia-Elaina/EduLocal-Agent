"""
EduLocal Agent 配置管理模块
负责读取 settings.yaml 并创建数据目录
"""

from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
import yaml


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "deepseek"
    api_key: str = ""
    base_url: Optional[str] = None
    model_name: str = "deepseek-chat"
    temperature: float = 0.7


class EmbeddingConfig(BaseModel):
    """Embedding 配置"""
    provider: str = "local"
    model_name: str = "BAAI/bge-small-zh-v1.5"


class LocalLLMConfig(BaseModel):
    """本地 LLM 配置"""
    ollama_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"


class RAGConfig(BaseModel):
    """RAG 配置"""
    top_k: int = 5
    hybrid_weights: List[float] = [0.6, 0.4]
    use_reranker: bool = False
    max_context_tokens: int = 2000


class HarnessConfig(BaseModel):
    """Harness 工程配置"""
    enable_tracing: bool = True
    max_conversation_turns: int = 10
    rate_limit_calls_per_minute: int = 30


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 7860


class Settings:
    """全局配置（非 Pydantic，更灵活）"""

    def __init__(self):
        # 子配置
        self.llm = LLMConfig()
        self.embedding = EmbeddingConfig()
        self.local_llm = LocalLLMConfig()
        self.rag = RAGConfig()
        self.harness = HarnessConfig()
        self.server = ServerConfig()

        # 数据目录
        self.data_dir = Path.home() / "EduLocalData"
        self.chroma_db_dir: Optional[Path] = None
        self.sqlite_dir: Optional[Path] = None
        self.cache_dir: Optional[Path] = None
        self.logs_dir: Optional[Path] = None
        self.knowledge_base_dir: Optional[Path] = None

    def setup_directories(self):
        """创建所有数据目录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 设置子目录
        self.chroma_db_dir = self.data_dir / "chroma_db"
        self.sqlite_dir = self.data_dir / "sqlite"
        self.cache_dir = self.data_dir / "cache"
        self.logs_dir = self.data_dir / "logs"
        self.knowledge_base_dir = self.data_dir / "knowledge_base"

        # 创建所有子目录
        for dir_path in [
            self.chroma_db_dir,
            self.sqlite_dir,
            self.cache_dir,
            self.logs_dir,
            self.logs_dir / "traces",
            self.knowledge_base_dir,
            self.data_dir / "configs"
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


# 全局设置实例
_settings: Optional[Settings] = None


def load_settings_from_yaml(yaml_path: str = None) -> Settings:
    """从 YAML 文件加载配置"""
    settings = Settings()

    # 先设置目录
    settings.setup_directories()

    # 优先从用户数据目录加载配置
    user_config_path = settings.data_dir / "configs" / "settings.yaml"
    project_config_path = Path(__file__).parent.parent.parent.parent / "configs" / "settings.yaml"

    # 确定使用哪个配置文件
    config_path = None
    if user_config_path.exists():
        config_path = user_config_path
    elif project_config_path.exists():
        config_path = project_config_path
    elif yaml_path and Path(yaml_path).exists():
        config_path = Path(yaml_path)

    if config_path:
        print(f"[Config] 加载配置文件: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # 更新配置
        if "llm" in config_data:
            settings.llm = LLMConfig(**config_data["llm"])
        if "embedding" in config_data:
            settings.embedding = EmbeddingConfig(**config_data["embedding"])
        if "local_llm" in config_data:
            settings.local_llm = LocalLLMConfig(**config_data["local_llm"])
        if "rag" in config_data:
            settings.rag = RAGConfig(**config_data["rag"])
        if "harness" in config_data:
            settings.harness = HarnessConfig(**config_data["harness"])
        if "server" in config_data:
            settings.server = ServerConfig(**config_data["server"])
    else:
        print("[Config] 未找到配置文件，使用默认配置")

    return settings


def get_settings() -> Settings:
    """获取全局配置（单例）"""
    global _settings
    if _settings is None:
        _settings = load_settings_from_yaml()
    return _settings
