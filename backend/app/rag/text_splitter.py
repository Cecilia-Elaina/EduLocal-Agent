"""
文档分块器（增强版）
智能分块，保持语义完整性
"""

from typing import List, Optional
from langchain_core.documents import Document
from loguru import logger


class TextSplitter:
    """文档分块器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        min_chunk_size: int = 50,
        separators: Optional[List[str]] = None,
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每个分块的最大字符数
            chunk_overlap: 分块之间的重叠字符数
            min_chunk_size: 最小分块大小
            separators: 分割符列表
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";", " "]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档列表

        Args:
            documents: 原始文档列表

        Returns:
            分块后的文档列表
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        # 根据语言选择分割符
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            add_start_index=True,
            separators=self.separators,
        )

        chunks = splitter.split_documents(documents)

        # 过滤太小的分块
        chunks = [chunk for chunk in chunks if len(chunk.page_content) >= self.min_chunk_size]

        # 为每个分块添加序号
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        logger.info(f"文档分块完成: {len(documents)} 文档 -> {len(chunks)} 分块")
        return chunks

    def split_by_headings(self, documents: List[Document]) -> List[Document]:
        """
        按标题分割文档

        Args:
            documents: 原始文档列表

        Returns:
            分块后的文档列表
        """
        chunks = []

        for doc in documents:
            content = doc.page_content
            lines = content.split("\n")

            current_chunk = []
            current_heading = ""

            for line in lines:
                # 检测标题行（#开头或全大写）
                if line.startswith("#") or (line.isupper() and len(line) < 100):
                    # 保存当前分块
                    if current_chunk:
                        chunk_content = "\n".join(current_chunk).strip()
                        if len(chunk_content) >= self.min_chunk_size:
                            chunks.append(Document(
                                page_content=chunk_content,
                                metadata={
                                    **doc.metadata,
                                    "heading": current_heading,
                                }
                            ))
                    current_heading = line
                    current_chunk = []
                else:
                    current_chunk.append(line)

            # 保存最后一个分块
            if current_chunk:
                chunk_content = "\n".join(current_chunk).strip()
                if len(chunk_content) >= self.min_chunk_size:
                    chunks.append(Document(
                        page_content=chunk_content,
                        metadata={
                            **doc.metadata,
                            "heading": current_heading,
                        }
                    ))

        # 为每个分块添加序号
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)

        logger.info(f"按标题分块完成: {len(documents)} 文档 -> {len(chunks)} 分块")
        return chunks


def split_documents(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[Document]:
    """便捷函数：分割文档"""
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)
