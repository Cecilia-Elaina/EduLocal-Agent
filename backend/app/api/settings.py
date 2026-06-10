"""
设置 API
管理配置、模型切换
"""

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

router = APIRouter()


class LLMSettings(BaseModel):
    """LLM 设置"""
    provider: str
    api_key: Optional[str] = None
    model_name: str
    base_url: Optional[str] = None
    temperature: float = 0.7


class SettingsResponse(BaseModel):
    """设置响应"""
    llm_provider: str
    llm_model: str
    has_api_key: bool
    embedding_model: str
    rag_top_k: int


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """获取当前设置"""
    from backend.app.config import get_settings as get_config

    settings = get_config()

    return SettingsResponse(
        llm_provider=settings.llm.provider,
        llm_model=settings.llm.model_name,
        has_api_key=bool(settings.llm.api_key),
        embedding_model=settings.embedding.model_name,
        rag_top_k=settings.rag.top_k,
    )


@router.get("/models")
async def get_models(provider: str = "deepseek"):
    """获取可用模型列表"""
    from backend.app.config import get_settings as get_config

    settings = get_config()

    try:
        if provider == "deepseek":
            import httpx
            api_key = settings.llm.api_key
            if not api_key:
                return {"models": [], "error": "请先配置 API Key"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.deepseek.com/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return {"models": models}
                else:
                    return {"models": [], "error": f"获取模型列表失败: {response.status_code}"}

        elif provider == "openai":
            import httpx
            api_key = settings.llm.api_key
            if not api_key:
                return {"models": [], "error": "请先配置 API Key"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    models = [m["id"] for m in data.get("data", []) if "gpt" in m["id"].lower()]
                    return {"models": sorted(models)}
                else:
                    return {"models": [], "error": f"获取模型列表失败: {response.status_code}"}

        elif provider == "ollama":
            import httpx
            ollama_url = settings.local_llm.ollama_url
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {"models": models}
                else:
                    return {"models": [], "error": "Ollama 未运行"}

        return {"models": []}

    except Exception as e:
        logger.error(f"[Settings] 获取模型列表失败: {e}")
        return {"models": [], "error": str(e)}


@router.put("/llm")
async def update_llm_settings(llm_settings: LLMSettings):
    """更新 LLM 设置"""
    from backend.app.config import get_settings as get_config
    from backend.app.models import LLMFactory

    settings = get_config()

    logger.info(f"[Settings] 更新 LLM 设置: {llm_settings.provider}/{llm_settings.model_name}")

    # 更新内存中的配置
    settings.llm.provider = llm_settings.provider
    settings.llm.model_name = llm_settings.model_name
    settings.llm.temperature = llm_settings.temperature

    if llm_settings.api_key:
        settings.llm.api_key = llm_settings.api_key
        logger.info(f"[Settings] API Key 已更新")

    if llm_settings.base_url:
        settings.llm.base_url = llm_settings.base_url
    elif llm_settings.provider == "deepseek":
        settings.llm.base_url = "https://api.deepseek.com"
    elif llm_settings.provider == "openai":
        settings.llm.base_url = None  # 使用默认

    # 重置 LLM 实例，下次调用时会重新创建
    LLMFactory.reset()

    # 保存到配置文件
    _save_settings(settings)

    return {"status": "success", "message": "LLM 设置已更新"}


@router.get("/status")
async def get_status():
    """获取系统状态"""
    from backend.app.config import get_settings as get_config
    from backend.app.models import get_database

    settings = get_config()
    db = get_database()
    stats = db.get_stats()

    # 检查 Ollama 是否可用
    ollama_available = False
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.local_llm.ollama_url}/api/tags", timeout=2)
            ollama_available = response.status_code == 200
    except Exception:
        pass

    return {
        "llm_provider": settings.llm.provider,
        "llm_model": settings.llm.model_name,
        "has_api_key": bool(settings.llm.api_key),
        "ollama_available": ollama_available,
        "data_dir": str(settings.data_dir),
        "stats": stats,
    }


def _save_settings(settings):
    """保存设置到配置文件"""
    settings_data = {
        "llm": {
            "provider": settings.llm.provider,
            "api_key": settings.llm.api_key,
            "model_name": settings.llm.model_name,
            "base_url": settings.llm.base_url,
            "temperature": settings.llm.temperature,
        },
        "embedding": {
            "provider": settings.embedding.provider,
            "model_name": settings.embedding.model_name,
        },
        "local_llm": {
            "ollama_url": settings.local_llm.ollama_url,
            "model": settings.local_llm.model,
        },
        "rag": {
            "top_k": settings.rag.top_k,
            "hybrid_weights": settings.rag.hybrid_weights,
            "use_reranker": settings.rag.use_reranker,
            "max_context_tokens": settings.rag.max_context_tokens,
        },
    }

    # 保存到用户数据目录
    config_path = settings.data_dir / "configs" / "settings.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(settings_data, f, allow_unicode=True, default_flow_style=False)

    logger.info(f"[Settings] 配置已保存到: {config_path}")
