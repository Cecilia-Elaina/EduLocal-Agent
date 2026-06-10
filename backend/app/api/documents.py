"""
文档管理 API
使用 SQLite 持久化存储
"""

import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from pathlib import Path
from loguru import logger

router = APIRouter()


class DocumentInfo(BaseModel):
    """文档信息"""
    id: str
    filename: str
    chunk_count: int
    created_at: str


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentInfo]
    total: int


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传并索引文档

    支持格式: PDF, TXT, Markdown, Word
    """
    from backend.app.config import get_settings
    from backend.app.models import get_database
    from backend.app.rag import load_document, get_vector_store

    # 检查文件格式
    allowed_extensions = {".pdf", ".txt", ".md", ".docx", ".doc"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}\n支持的格式: {allowed_extensions}"
        )

    logger.info(f"[Documents] 上传文件: {file.filename}")

    try:
        settings = get_settings()
        db = get_database()

        # 保存文件到知识库目录
        save_dir = settings.knowledge_base_dir
        save_path = save_dir / file.filename

        # 读取文件内容
        content = await file.read()
        save_path.write_bytes(content)

        # 计算文件哈希
        file_hash = hashlib.md5(content).hexdigest()
        doc_id = file_hash[:8]

        # 加载文档
        documents = load_document(str(save_path))

        # 添加到向量存储
        vector_store = get_vector_store()
        chunk_count = vector_store.add_documents(
            documents,
            metadata={"filename": file.filename, "file_hash": file_hash}
        )

        # 保存到数据库
        db.add_document(
            doc_id=doc_id,
            filename=file.filename,
            file_path=str(save_path),
            file_hash=file_hash,
            chunk_count=chunk_count,
        )

        logger.info(f"[Documents] 索引完成: {file.filename} -> {chunk_count} 个分块")

        return {
            "status": "success",
            "message": f"文档 {file.filename} 索引成功",
            "document_id": doc_id,
            "chunk_count": chunk_count,
        }

    except Exception as e:
        logger.error(f"[Documents] 索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """获取已索引文档列表"""
    from backend.app.models import get_database

    db = get_database()
    docs = db.get_documents()

    documents = [
        DocumentInfo(
            id=doc["id"],
            filename=doc["filename"],
            chunk_count=doc["chunk_count"],
            created_at=doc["created_at"],
        )
        for doc in docs
    ]

    return DocumentListResponse(
        documents=documents,
        total=len(documents),
    )


@router.get("/{document_id}")
async def get_document(document_id: str):
    """获取文档详情"""
    from backend.app.models import get_database

    db = get_database()
    doc = db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    return doc


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    from backend.app.models import get_database

    db = get_database()
    doc = db.get_document(document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除原始文件
    file_path = Path(doc["file_path"])
    if file_path.exists():
        file_path.unlink()

    # 删除数据库记录
    db.delete_document(document_id)

    logger.info(f"[Documents] 删除文档: {doc['filename']}")

    return {"status": "deleted", "document_id": document_id}
