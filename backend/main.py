"""
EduLocal Agent - 主入口
桌面级智能教学助理
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.config import get_settings


# 配置日志
def setup_logging():
    """配置 loguru 日志"""
    settings = get_settings()

    # 移除默认处理器
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # 文件输出
    log_file = settings.logs_dir / "app.log"
    logger.add(
        str(log_file),
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        level="DEBUG"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    from backend.app.models import get_database

    # 启动时
    settings = get_settings()
    setup_logging()

    logger.info("=" * 50)
    logger.info("EduLocal Agent 启动中...")
    logger.info(f"数据目录: {settings.data_dir}")
    logger.info(f"LLM 提供商: {settings.llm.provider}")

    # 初始化数据库
    db = get_database()
    stats = db.get_stats()
    logger.info(f"数据库统计: {stats}")
    logger.info("=" * 50)

    yield

    # 关闭时
    db = get_database()
    db.close()
    logger.info("EduLocal Agent 关闭")


app = FastAPI(
    title="EduLocal Agent",
    description="桌面级智能教学助理 API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康检查"""
    settings = get_settings()
    return {
        "name": "EduLocal Agent",
        "version": "0.1.0",
        "status": "running",
        "data_dir": str(settings.data_dir)
    }


@app.get("/health")
async def health():
    """健康检查接口"""
    settings = get_settings()
    return {
        "status": "healthy",
        "llm_provider": settings.llm.provider,
        "data_dir_exists": settings.data_dir.exists()
    }


# 导入并注册 API 路由
from backend.app.api import router as api_router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True
    )
