"""
RAG 模块单元测试
"""

import pytest
from pathlib import Path
from backend.app.rag.text_splitter import TextSplitter, split_documents
from backend.app.rag.document_loader import DocumentLoader
from langchain_core.documents import Document


class TestTextSplitter:
    """文本分块器测试"""

    def test_split_empty(self):
        """测试空文档分块"""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = splitter.split_documents([])
        assert chunks == []

    def test_split_short_text(self):
        """测试短文本分块"""
        doc = Document(page_content="这是一个短文本测试，内容足够长以通过最小分块大小检查", metadata={"source": "test"})
        splitter = TextSplitter(chunk_size=1000, chunk_overlap=10, min_chunk_size=5)
        chunks = splitter.split_documents([doc])
        assert len(chunks) >= 1

    def test_split_long_text(self):
        """测试长文本分块"""
        # 创建一个长文本
        long_text = "这是一段测试文本，用于验证分块功能是否正常工作。" * 20
        doc = Document(page_content=long_text, metadata={"source": "test"})

        splitter = TextSplitter(chunk_size=200, chunk_overlap=20, min_chunk_size=10)
        chunks = splitter.split_documents([doc])

        assert len(chunks) > 1

    def test_split_preserves_metadata(self):
        """测试分块保留元数据"""
        doc = Document(
            page_content="测试内容，这是一段足够长的文本用于测试分块功能，确保元数据被正确保留，包含足够的字符数",
            metadata={"source": "test.pdf", "page": 1}
        )
        splitter = TextSplitter(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        chunks = splitter.split_documents([doc])

        assert len(chunks) > 0
        assert chunks[0].metadata["source"] == "test.pdf"


class TestDocumentLoader:
    """文档加载器测试"""

    def test_supported_extensions(self):
        """测试支持的文件格式"""
        supported = DocumentLoader.SUPPORTED_EXTENSIONS
        assert ".pdf" in supported
        assert ".txt" in supported
        assert ".md" in supported
        assert ".docx" in supported

    def test_load_txt(self):
        """测试加载 TXT 文件"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "test.txt"
            txt_file.write_text("这是测试内容，这是一段足够长的文本用于测试文档加载功能，确保能够正确读取文件内容并返回文档对象", encoding="utf-8")

            docs = DocumentLoader.load(str(txt_file))
            assert len(docs) >= 1
            assert "测试内容" in docs[0].page_content

    def test_load_markdown(self):
        """测试加载 Markdown 文件"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("# 标题\n\n这是内容", encoding="utf-8")

            docs = DocumentLoader.load(str(md_file))
            assert len(docs) >= 1

    def test_load_nonexistent(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            DocumentLoader.load("/nonexistent/file.txt")

    def test_load_unsupported_format(self, temp_dir):
        """测试加载不支持的格式"""
        xyz_file = temp_dir / "test.xyz"
        xyz_file.write_text("内容", encoding="utf-8")

        with pytest.raises(ValueError):
            DocumentLoader.load(str(xyz_file))
