import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
from langchain_core.documents.base import Document

from app.schemas.documents import ChunkMetadata
from app.services.document_service import DocumentService


class TestDocumentService:
    """
    * test suite for document service
    """

    @pytest.fixture
    def document_service(self):
        """
        * create document service instance for testing
        """
        with (
            patch("app.services.document_service.QdrantVectorStore") as mock_vector,
            patch("app.services.document_service.EmbeddingService") as mock_embedding,
        ):
            # * setup mocks
            mock_vector.return_value.upsert_points = Mock()
            mock_embedding.return_value.generate_embeddings_batch = AsyncMock(
                return_value=[[0.1, 0.2, 0.3]] * 3  # * mock embeddings
            )

            service = DocumentService()
            return service

    @pytest.fixture
    def sample_text_file(self):
        """
        * create temporary text file for testing
        """
        content = (
            "This is a test document.\nIt has multiple lines.\nFor testing purposes."
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # * cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def sample_pdf_file(self):
        """
        * create temporary pdf file path for testing
        """
        # * note: this would need actual pdf content in real tests
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        yield temp_path

        # * cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def mock_langchain_documents(self):
        """
        * mock langchain document objects
        """
        return [
            Document(
                page_content="This is page 1 content.",
                metadata={"source": "test.pdf", "page_label": 1},
            ),
            Document(
                page_content="This is page 2 content.",
                metadata={"source": "test.pdf", "page_label": 2},
            ),
        ]

    @pytest.mark.asyncio
    async def test_process_document_text_file(self, document_service, sample_text_file):
        """
        * test processing text file
        """
        with patch.object(document_service, "_extract_content") as mock_extract:
            mock_extract.return_value = [
                Document(
                    page_content="This is a test document.",
                    metadata={"source": sample_text_file},
                )
            ]

            result = await document_service.process_document(
                file_path=sample_text_file,
                filename="test.txt",
                content_type="text/plain",
            )

            assert result.filename == "test.txt"
            assert result.content_type == "text/plain"
            assert result.chunks_created > 0

    @pytest.mark.asyncio
    async def test_extract_content_text_file(self, document_service, sample_text_file):
        """
        * test text file content extraction
        """
        with patch("app.services.document_service.TextLoader") as mock_loader:
            mock_loader.return_value.load.return_value = [
                Document(
                    page_content="test content", metadata={"source": sample_text_file}
                )
            ]

            result = await document_service._extract_content(
                sample_text_file, "text/plain"
            )

            assert len(result) == 1
            mock_loader.assert_called_once_with(sample_text_file, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_extract_content_pdf_file(self, document_service, sample_pdf_file):
        """
        * test pdf file content extraction
        """
        with patch("app.services.document_service.PyPDFLoader") as mock_loader:
            mock_loader.return_value.load.return_value = [
                Document(
                    page_content="pdf content",
                    metadata={"source": sample_pdf_file, "page_label": 1},
                )
            ]

            result = await document_service._extract_content(
                sample_pdf_file, "application/pdf"
            )

            assert len(result) == 1
            mock_loader.assert_called_once_with(sample_pdf_file)

    @pytest.mark.asyncio
    async def test_extract_content_docx_file(self, document_service):
        """
        * test docx file content extraction
        """
        docx_path = "test.docx"

        with patch(
            "app.services.document_service.UnstructuredWordDocumentLoader"
        ) as mock_loader:
            mock_loader.return_value.load.return_value = [
                Document(
                    page_content="docx content",
                    metadata={"source": docx_path, "page_number": 1},
                )
            ]

            result = await document_service._extract_content(
                docx_path,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            assert len(result) == 1
            mock_loader.assert_called_once_with(docx_path, mode="paged")

    @pytest.mark.asyncio
    async def test_extract_content_unsupported_type(self, document_service):
        """
        * test unsupported file type raises error
        """
        with pytest.raises(ValueError, match="Unsupported file type"):
            await document_service._extract_content("test.xyz", "application/xyz")

    def test_clean_content(self, document_service):
        """
        * test content cleaning functionality
        """
        dirty_text = "  'This  is   a test.This needs cleaning.'  "
        cleaned = document_service._clean_content(dirty_text)

        assert cleaned == "This is a test. This needs cleaning."
        assert not cleaned.startswith("'")
        assert not cleaned.endswith("'")

    def test_clean_content_with_numbering(self, document_service):
        """
        * test content cleaning with numbered lists
        """
        text_with_numbers = "Here are items: 1. First item 2. Second item 3. Third item"
        cleaned = document_service._clean_content(text_with_numbers)

        assert "\n1. First item" in cleaned
        assert "\n2. Second item" in cleaned

    @pytest.mark.asyncio
    async def test_create_chunks(self, document_service, mock_langchain_documents):
        """
        * test chunk creation with metadata
        """
        with patch.object(
            document_service.text_splitter, "split_documents"
        ) as mock_split:
            mock_split.return_value = [
                Document(
                    page_content="Chunk 1 content",
                    metadata={"source": "test.pdf", "page_label": 1},
                ),
                Document(
                    page_content="Chunk 2 content",
                    metadata={"source": "test.pdf", "page_label": 2},
                ),
            ]

            chunks = await document_service._create_chunks(
                mock_langchain_documents, "application/pdf"
            )

            assert len(chunks) == 2
            assert all(isinstance(chunk, ChunkMetadata) for chunk in chunks)
            assert chunks[0].chunk_index == 0
            assert chunks[1].chunk_index == 1

    def test_extract_page_number_pdf(self, document_service):
        """
        * test page number extraction for pdf files
        """
        doc = Document(page_content="test", metadata={"page_label": 5})

        page_num = document_service._extract_page_number(doc, "application/pdf")
        assert page_num == 5

    def test_extract_page_number_docx(self, document_service):
        """
        * test page number extraction for docx files
        """
        doc = Document(page_content="test", metadata={"page_number": 3})

        page_num = document_service._extract_page_number(
            doc,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert page_num == 3

    def test_extract_page_number_text_file(self, document_service):
        """
        * test page number extraction for text files returns none
        """
        doc = Document(page_content="test", metadata={"source": "test.txt"})

        page_num = document_service._extract_page_number(doc, "text/plain")
        assert page_num is None

    def test_extract_page_number_fallback(self, document_service):
        """
        * test page number extraction fallback to 1
        """
        doc = Document(page_content="test", metadata={"source": "test.pdf"})

        page_num = document_service._extract_page_number(doc, "application/pdf")
        assert page_num == 1

    @pytest.mark.asyncio
    async def test_process_document_with_embeddings_and_vector_store(
        self, document_service
    ):
        """
        * test full document processing including embeddings and vector storage
        """
        with (
            patch.object(document_service, "_extract_content") as mock_extract,
            patch.object(document_service, "_create_chunks") as mock_chunks,
        ):
            # * setup mocks
            mock_extract.return_value = [
                Document(page_content="test content", metadata={"source": "test.txt"})
            ]

            mock_chunk = Mock()
            mock_chunk.content = "test chunk content"
            mock_chunks.return_value = [mock_chunk]

            result = await document_service.process_document(
                file_path="test.txt", filename="test.txt", content_type="text/plain"
            )

            # * verify embedding service was called
            document_service.embedding_service.generate_embeddings_batch.assert_called_once()

            # * verify vector store was called
            document_service.vector_service.upsert_points.assert_called_once()

            assert result.filename == "test.txt"

    @pytest.mark.asyncio
    async def test_process_document_error_handling(self, document_service):
        """
        * test error handling in document processing
        """
        with patch.object(document_service, "_extract_content") as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")

            # * should not raise exception but log error
            result = await document_service.process_document(
                file_path="nonexistent.txt",
                filename="test.txt",
                content_type="text/plain",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_create_chunks_empty_content_filtering(self, document_service):
        """
        * test that empty chunks are filtered out
        """
        with patch.object(
            document_service.text_splitter, "split_documents"
        ) as mock_split:
            mock_split.return_value = [
                Document(page_content="", metadata={"source": "test.txt"}),  # * empty
                Document(
                    page_content="   ", metadata={"source": "test.txt"}
                ),  # * whitespace only
                Document(
                    page_content="Valid content", metadata={"source": "test.txt"}
                ),  # * valid
            ]

            chunks = await document_service._create_chunks(
                [Document(page_content="test", metadata={})], "text/plain"
            )

            # * only the valid chunk should remain
            assert len(chunks) == 1
            assert "Valid content" in chunks[0].content
