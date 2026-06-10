"""
混合检索器
结合语义检索和关键词检索，提升召回率
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from loguru import logger

from backend.app.config import get_settings
from backend.app.rag.vector_store import get_vector_store


class HybridRetriever:
    """混合检索器"""

    def __init__(self):
        self._settings = get_settings()
        self._vector_store = get_vector_store()
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_docs: List[Document] = []

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """
        混合检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关文档列表
        """
        if top_k is None:
            top_k = self._settings.rag.top_k

        # 获取权重
        semantic_weight, keyword_weight = self._settings.rag.hybrid_weights

        logger.debug(f"混合检索: query='{query[:50]}...', top_k={top_k}")

        # 1. 语义检索
        semantic_results = self._vector_store.search(query, top_k=top_k * 2)

        # 2. 关键词检索（BM25）
        keyword_results = self._bm25_search(query, top_k=top_k * 2)

        # 3. 融合去重
        merged_results = self._merge_results(
            semantic_results,
            keyword_results,
            semantic_weight,
            keyword_weight,
            top_k,
        )

        logger.debug(f"混合检索返回 {len(merged_results)} 个结果")
        return merged_results

    def _bm25_search(self, query: str, top_k: int) -> List[Document]:
        """BM25 关键词检索"""
        # 简单的中文分词（按字符分割）
        query_tokens = list(query)

        if not self._bm25_docs:
            # 从向量存储加载所有文档建立索引
            # 注意：生产环境应使用增量索引
            logger.debug("建立 BM25 索引...")
            collection = self._vector_store.store._collection
            all_docs = collection.get()

            if all_docs and all_docs["documents"]:
                self._bm25_docs = [
                    Document(
                        page_content=doc,
                        metadata=meta or {}
                    )
                    for doc, meta in zip(
                        all_docs["documents"],
                        all_docs["metadatas"]
                    )
                ]

        if not self._bm25_docs:
            return []

        # 构建 BM25 索引
        corpus_tokens = [list(doc.page_content) for doc in self._bm25_docs]
        bm25 = BM25Okapi(corpus_tokens)

        # 检索
        scores = bm25.get_scores(query_tokens)
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        return [self._bm25_docs[i] for i in top_indices if scores[i] > 0]

    def _merge_results(
        self,
        semantic_results: List[Document],
        keyword_results: List[Document],
        semantic_weight: float,
        keyword_weight: float,
        top_k: int,
    ) -> List[Document]:
        """
        融合两路检索结果

        使用加权 RRF (Reciprocal Rank Fusion) 算法
        """
        # 文档 -> 综合得分
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        # 语义检索结果
        for rank, doc in enumerate(semantic_results):
            doc_id = self._get_doc_id(doc)
            score = semantic_weight / (rank + 1)  # RRF
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score
            doc_map[doc_id] = doc

        # 关键词检索结果
        for rank, doc in enumerate(keyword_results):
            doc_id = self._get_doc_id(doc)
            score = keyword_weight / (rank + 1)  # RRF
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        # 按得分排序
        sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

        return [doc_map[doc_id] for doc_id in sorted_ids[:top_k]]

    def _get_doc_id(self, doc: Document) -> str:
        """生成文档唯一标识"""
        source = doc.metadata.get("source", "")
        content_hash = hash(doc.page_content[:100])
        return f"{source}_{content_hash}"


def get_retriever() -> HybridRetriever:
    """获取全局检索器实例"""
    return HybridRetriever()
