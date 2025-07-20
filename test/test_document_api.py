import io
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes.document import router
from app.schemas.documents import ProcessedDocument


@pytest.fixture
def client():
    """
    * create test client
    """
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_document_service():
    """
    * mock document service for testing
    """
    mock_service = Mock()
    mock_processed_doc = Mock(spec=ProcessedDocument)
    mock_processed_doc.filename = "test.txt"
    mock_processed_doc.chunks_created = 5
    mock_processed_doc.content_type = "text/plain"
    mock_processed_doc.created_at = None

    mock_service.process_document = AsyncMock(return_value=mock_processed_doc)
    return mock_service


@pytest.fixture
def sample_text_file():
    """
    * create sample text file for upload testing
    """
    content = b"This is a test document content for upload testing."
    return ("test.txt", io.BytesIO(content), "text/plain")


@pytest.fixture
def sample_pdf_file():
    """
    * create sample pdf file for upload testing
    """
    content = b"%PDF-1.4 fake pdf content for testing"
    return ("test.pdf", io.BytesIO(content), "application/pdf")


@pytest.fixture
def sample_docx_file():
    """
    * create sample docx file for upload testing
    """
    content = b"fake docx content for testing"
    return (
        "test.docx",
        io.BytesIO(content),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


class TestDocumentAPI:
    """
    * test suite for document api endpoints
    """

    def test_upload_document_success(
        self, client, sample_text_file, mock_document_service
    ):
        """
        * test successful single document upload
        """
        filename, file_content, content_type = sample_text_file

        with patch(
            "app.api.document.get_document_service", return_value=mock_document_service
        ):
            response = client.post(
                "/documents/upload",
                files={"file": (filename, file_content, content_type)},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["filename"] == "test.txt"
            assert data["data"]["chunks_created"] == 5
            assert data["data"]["content_type"] == "text/plain"

    def test_upload_document_pdf_success(
        self, client, sample_pdf_file, mock_document_service
    ):
        """
        * test successful pdf document upload
        """
        filename, file_content, content_type = sample_pdf_file

        with patch(
            "app.api.v1.routes.document.get_document_service",
            return_value=mock_document_service,
        ):
            response = client.post(
                "/documents/upload",
                files={"file": (filename, file_content, content_type)},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"

    def test_upload_document_docx_success(
        self, client, sample_docx_file, mock_document_service
    ):
        """
        * test successful docx document upload
        """
        filename, file_content, content_type = sample_docx_file

        with patch(
            "app.api.v1.routes.document.get_document_service",
            return_value=mock_document_service,
        ):
            response = client.post(
                "/documents/upload",
                files={"file": (filename, file_content, content_type)},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"

    def test_upload_document_unsupported_type(self, client):
        """
        * test upload with unsupported file type
        """
        filename = "test.xyz"
        content = io.BytesIO(b"unsupported content")
        content_type = "application/xyz"

        response = client.post(
            "/documents/upload", files={"file": (filename, content, content_type)}
        )

        assert response.status_code == 400
        data = response.json()
        assert "unsupported file type" in data["detail"]

    @patch("app.api.document.settings")
    def test_upload_document_file_too_large(
        self, mock_settings, client, sample_text_file
    ):
        """
        * test upload with file size exceeding limit
        """
        mock_settings.max_file_size = 10  # * very small limit
        filename, file_content, content_type = sample_text_file

        response = client.post(
            "/documents/upload", files={"file": (filename, file_content, content_type)}
        )

        assert response.status_code == 413
        data = response.json()
        assert "file size exceeds" in data["detail"]

    def test_upload_document_processing_error(self, client, sample_text_file):
        """
        * test upload when document processing fails
        """
        filename, file_content, content_type = sample_text_file

        mock_service = Mock()
        mock_service.process_document = AsyncMock(
            side_effect=Exception("Processing failed")
        )

        with patch("app.api.document.get_document_service", return_value=mock_service):
            response = client.post(
                "/documents/upload",
                files={"file": (filename, file_content, content_type)},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "document processing failed"

    def test_upload_multiple_documents_success(self, client, mock_document_service):
        """
        * test successful multiple document upload
        """
        files = [
            ("test1.txt", io.BytesIO(b"content 1"), "text/plain"),
            ("test2.txt", io.BytesIO(b"content 2"), "text/plain"),
        ]

        with patch(
            "app.api.document.get_document_service", return_value=mock_document_service
        ):
            response = client.post(
                "/documents/upload-multiple",
                files=[
                    ("files", (name, content, ctype)) for name, content, ctype in files
                ],
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "completed"
            assert data["data"]["successful_count"] == 2
            assert data["data"]["failed_count"] == 0

    def test_upload_multiple_documents_mixed_results(self, client):
        """
        * test multiple upload with some successes and failures
        """
        files = [
            ("test1.txt", io.BytesIO(b"content 1"), "text/plain"),
            ("test2.xyz", io.BytesIO(b"content 2"), "application/xyz"),  # * unsupported
        ]

        mock_service = Mock()
        mock_processed_doc = Mock(spec=ProcessedDocument)
        mock_processed_doc.filename = "test1.txt"
        mock_processed_doc.chunks_created = 3
        mock_processed_doc.content_type = "text/plain"
        mock_service.process_document = AsyncMock(return_value=mock_processed_doc)

        with patch("app.api.document.get_document_service", return_value=mock_service):
            response = client.post(
                "/documents/upload-multiple",
                files=[
                    ("files", (name, content, ctype)) for name, content, ctype in files
                ],
            )

            assert response.status_code == 201
            data = response.json()
            assert data["data"]["successful_count"] == 1
            assert data["data"]["failed_count"] == 1
            assert len(data["data"]["successful"]) == 1
            assert len(data["data"]["failed"]) == 1

    @patch("app.api.document.settings")
    def test_upload_multiple_documents_too_many_files(self, mock_settings, client):
        """
        * test multiple upload with too many files
        """
        mock_settings.max_bulk_upload_count = 2

        files = [
            ("test1.txt", io.BytesIO(b"content 1"), "text/plain"),
            ("test2.txt", io.BytesIO(b"content 2"), "text/plain"),
            ("test3.txt", io.BytesIO(b"content 3"), "text/plain"),  # * exceeds limit
        ]

        response = client.post(
            "/documents/upload-multiple",
            files=[("files", (name, content, ctype)) for name, content, ctype in files],
        )

        assert response.status_code == 400
        data = response.json()
        assert "too many files" in data["detail"]

    def test_upload_multiple_documents_processing_error(self, client):
        """
        * test multiple upload when some documents fail processing
        """
        files = [
            ("test1.txt", io.BytesIO(b"content 1"), "text/plain"),
            ("test2.txt", io.BytesIO(b"content 2"), "text/plain"),
        ]

        mock_service = Mock()
        # * first call succeeds, second fails
        mock_processed_doc = Mock(spec=ProcessedDocument)
        mock_processed_doc.filename = "test1.txt"
        mock_processed_doc.chunks_created = 3
        mock_processed_doc.content_type = "text/plain"

        mock_service.process_document = AsyncMock(
            side_effect=[mock_processed_doc, Exception("Processing failed for file 2")]
        )

        with patch("app.api.document.get_document_service", return_value=mock_service):
            response = client.post(
                "/documents/upload-multiple",
                files=[
                    ("files", (name, content, ctype)) for name, content, ctype in files
                ],
            )

            assert response.status_code == 201
            data = response.json()
            assert data["data"]["successful_count"] == 1
            assert data["data"]["failed_count"] == 1

    def test_upload_document_file_cleanup(
        self, client, sample_text_file, mock_document_service
    ):
        """
        * test that temporary files are cleaned up after processing
        """
        filename, file_content, content_type = sample_text_file

        with (
            patch(
                "app.api.document.get_document_service",
                return_value=mock_document_service,
            ),
            patch("app.api.document.os.path.exists", return_value=True) as mock_exists,
            patch("app.api.document.os.unlink") as mock_unlink,
        ):
            response = client.post(
                "/documents/upload",
                files={"file": (filename, file_content, content_type)},
            )

            assert response.status_code == 201
            # * verify cleanup was attempted
            mock_exists.assert_called()
            mock_unlink.assert_called()

    def test_upload_document_file_cleanup_on_error(self, client, sample_text_file):
        """
        * test that temporary files are cleaned up even when processing fails
        """
        filename, file_content, content_type = sample_text_file

        mock_service = Mock()
        mock_service.process_document = AsyncMock(
            side_effect=Exception("Processing failed")
        )

        with (
            patch("app.api.document.get_document_service", return_value=mock_service),
            patch("app.api.document.os.path.exists", return_value=True) as mock_exists,
            patch("app.api.document.os.unlink") as mock_unlink,
        ):
            response = client.post(
                "/documents/upload",
                files={"file": (filename, file_content, content_type)},
            )

            assert response.status_code == 500
            # * verify cleanup was attempted even on error
            mock_exists.assert_called()
            mock_unlink.assert_called()

    def test_dependency_injection(self, client):
        """
        * test that dependency injection works properly
        """
        with patch("app.api.document.DocumentService") as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance

            from app.api.document import get_document_service

            service = get_document_service()

            assert service == mock_instance
            mock_service_class.assert_called_once()
