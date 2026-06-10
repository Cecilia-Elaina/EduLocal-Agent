"""
API 路由模块
"""

from fastapi import APIRouter
from .chat import router as chat_router
from .documents import router as documents_router
from .settings import router as settings_router

router = APIRouter()

# 注册子路由
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(documents_router, prefix="/documents", tags=["documents"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
