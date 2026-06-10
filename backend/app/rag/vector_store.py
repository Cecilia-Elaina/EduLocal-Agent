"""
Chroma 向量存储管理
负责文档向量化、存储和检索
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from loguru import logger

from backend.app.config import get_settings
from backend.app.models import get_embeddings
from backend.app.rag.text_splitter import split_documents


class VectorStore:
    """Chroma 向量存储管理器"""

    def __init__(self):
        self._store: Optional[Chroma] = None
        self._settings = get_settings()

    @property
    def store(self) -> Chroma:
        """获取 Chroma 存储实例（懒加载）"""
        if self._store is None:
            self._store = self._create_store()
        return self._store

    def _create_store(self) -> Chroma:
        """创建 Chroma 存储"""
        embeddings = get_embeddings()
        persist_directory = str(self._settings.chroma_db_dir)

        logger.info(f"初始化 Chroma 向量存储: {persist_directory}")

        return Chroma(
            collection_name="edulocal_knowledge",
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

    def add_documents(
        self,
        documents: List[Document],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表
            metadata: 额外的元数据

        Returns:
            添加的分块数量
        """
        # 分块
        chunks = split_documents(documents)

        # 添加元数据
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)

        # 存储
        self.store.add_documents(chunks)
        logger.info(f"添加 {len(chunks)} 个文档分块到向量存储")

        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤

        Returns:
            相关文档列表
        """
        if top_k is None:
            top_k = self._settings.rag.top_k

        logger.debug(f"语义搜索: query='{query[:50]}...', top_k={top_k}")

        results = self.store.similarity_search(
            query=query,
            k=top_k,
            filter=filter_metadata,
        )

        logger.debug(f"搜索到 {len(results)} 个结果")
        return results

    def delete_by_source(self, source: str) -> int:
        """
        按来源删除文档

        Args:
            source: 文档来源路径

        Returns:
            删除的文档数量
        """
        # Chroma 暂不支持直接按条件删除，需要重建
        logger.warning("delete_by_source: Chroma 暂不支持条件删除，需要重建索引")
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        collection = self.store._collection
        return {
            "total_chunks": collection.count(),
            "persist_directory": str(self._settings.chroma_db_dir),
        }


# 全局实例
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取全局向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
