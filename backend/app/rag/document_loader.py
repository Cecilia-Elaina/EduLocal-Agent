"""
文档加载器（增强版）
支持更多格式，智能分块
"""

from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from loguru import logger


class DocumentLoader:
    """文档加载器"""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc", ".html", ".htm"}

    @classmethod
    def load(cls, file_path: str) -> List[Document]:
        """
        加载文档

        Args:
            file_path: 文件路径

        Returns:
            文档列表
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"不支持的文件格式: {path.suffix}\n"
                f"支持的格式: {cls.SUPPORTED_EXTENSIONS}"
            )

        logger.info(f"加载文档: {path.name}")

        loaders = {
            ".pdf": cls._load_pdf,
            ".txt": cls._load_text,
            ".md": cls._load_markdown,
            ".docx": cls._load_docx,
            ".doc": cls._load_doc,
            ".html": cls._load_html,
            ".htm": cls._load_html,
        }

        loader_func = loaders.get(path.suffix.lower())
        if loader_func:
            return loader_func(path)
        else:
            raise ValueError(f"未实现的文件格式: {path.suffix}")

    @classmethod
    def _load_pdf(cls, path: Path) -> List[Document]:
        """加载 PDF 文件"""
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(str(path))
        documents = loader.load()

        # 添加元数据
        for doc in documents:
            doc.metadata["filename"] = path.name
            doc.metadata["file_type"] = "pdf"

        logger.info(f"PDF 加载完成: {len(documents)} 页")
        return documents

    @classmethod
    def _load_text(cls, path: Path) -> List[Document]:
        """加载 TXT 文件"""
        from langchain_core.documents import Document

        content = path.read_text(encoding="utf-8")

        # 按段落分割
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        if not paragraphs:
            paragraphs = [content]

        documents = []
        for i, para in enumerate(paragraphs):
            if len(para) > 10:  # 过滤太短的段落
                documents.append(Document(
                    page_content=para,
                    metadata={
                        "source": str(path),
                        "filename": path.name,
                        "file_type": "txt",
                        "paragraph_index": i,
                    }
                ))

        logger.info(f"TXT 加载完成: {len(documents)} 个段落")
        return documents

    @classmethod
    def _load_markdown(cls, path: Path) -> List[Document]:
        """加载 Markdown 文件"""
        from langchain_core.documents import Document

        content = path.read_text(encoding="utf-8")

        # 按标题分割
        sections = []
        current_section = []
        current_title = ""

        for line in content.split("\n"):
            if line.startswith("#"):
                if current_section:
                    sections.append((current_title, "\n".join(current_section)))
                current_title = line
                current_section = []
            else:
                current_section.append(line)

        if current_section:
            sections.append((current_title, "\n".join(current_section)))

        documents = []
        for title, body in sections:
            full_content = f"{title}\n{body}".strip()
            if len(full_content) > 20:
                documents.append(Document(
                    page_content=full_content,
                    metadata={
                        "source": str(path),
                        "filename": path.name,
                        "file_type": "markdown",
                        "title": title.replace("#", "").strip(),
                    }
                ))

        if not documents:
            documents = [Document(
                page_content=content,
                metadata={
                    "source": str(path),
                    "filename": path.name,
                    "file_type": "markdown",
                }
            )]

        logger.info(f"Markdown 加载完成: {len(documents)} 个章节")
        return documents

    @classmethod
    def _load_docx(cls, path: Path) -> List[Document]:
        """加载 Word 文件"""
        from langchain_community.document_loaders import Docx2txtLoader

        loader = Docx2txtLoader(str(path))
        documents = loader.load()

        for doc in documents:
            doc.metadata["filename"] = path.name
            doc.metadata["file_type"] = "docx"

        logger.info(f"Word 文档加载完成: {len(documents)} 段")
        return documents

    @classmethod
    def _load_doc(cls, path: Path) -> List[Document]:
        """加载旧版 Word 文件"""
        # 尝试使用 antiword 或 textract
        try:
            import subprocess
            result = subprocess.run(
                ["antiword", str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if result.returncode == 0:
                from langchain_core.documents import Document
                return [Document(
                    page_content=result.stdout,
                    metadata={
                        "source": str(path),
                        "filename": path.name,
                        "file_type": "doc",
                    }
                )]
        except Exception:
            pass

        # 降级到 docx loader
        return cls._load_docx(path)

    @classmethod
    def _load_html(cls, path: Path) -> List[Document]:
        """加载 HTML 文件"""
        from langchain_community.document_loaders import UnstructuredHTMLLoader

        loader = UnstructuredHTMLLoader(str(path))
        documents = loader.load()

        for doc in documents:
            doc.metadata["filename"] = path.name
            doc.metadata["file_type"] = "html"

        logger.info(f"HTML 加载完成: {len(documents)} 段")
        return documents


def load_document(file_path: str) -> List[Document]:
    """便捷函数：加载文档"""
    return DocumentLoader.load(file_path)
