import os
import re
from typing import Any, Dict, List, Optional

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_core.documents.base import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.service_manager import service_manager
from app.schemas.documents import ChunkMetadata, ProcessedDocument
from app.utils.logger import LOGGER


class DocumentService:
    """
    * advanced document processor with metadata extraction
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            keep_separator=True,
        )
        self.vector_store = service_manager.get_vector_store()
        self.embedding_service = service_manager.get_embedding_service()

    async def process_document(
        self, file_path: str, filename: str, content_type: str
    ) -> ProcessedDocument:
        """
        * process document and create chunks with metadata
        """
        try:
            LOGGER.info(
                f"[Start] Processing document: {filename} (type={content_type})"
            )

            # * extract content based on file type
            documents = await self._extract_content(file_path, content_type)
            LOGGER.info(f"[Extracted] Total raw documents: {len(documents)}")

            if not documents:
                LOGGER.warning(f"No content extracted from file: {filename}")
                return None

            # * create chunks with cleaned content: ChunkMetadata data type
            chunks = await self._create_chunks(documents, content_type)
            LOGGER.info(f"[Chunked] Total chunks created: {len(chunks)}")

            if not chunks:
                LOGGER.warning(f"No chunks created from file: {filename}")
                return None

            # * embeddings
            chunk_texts = [chunk.document for chunk in chunks]
            LOGGER.info(
                f"[Embedding] Generating embeddings for {len(chunk_texts)} chunks"
            )
            embeddings = self.embedding_service.generate_embeddings_batch(
                chunk_texts, batch_size=8
            )

            if not embeddings or len(embeddings) != len(chunks):
                LOGGER.error(
                    f"Embedding generation failed or incomplete for file: {filename}"
                )
                return None

            # * upsert to qdrant
            self.vector_store.upsert_points(
                embeddings, [dict(chunk) for chunk in chunks]
            )
            LOGGER.info(
                f"[Upserted] Stored embeddings to vector DB for file: {filename}"
            )

            processed_doc = ProcessedDocument(
                filename=filename, chunks_created=len(chunks), content_type=content_type
            )

            LOGGER.info(
                f"[Success] Document processed: {filename} | chunks={len(chunks)}"
            )
            return processed_doc

        except Exception as e:
            LOGGER.exception(
                f"[Error] Document processing failed - {filename}: {str(e)}"
            )
            return None

    async def _extract_content(
        self, file_path: str, content_type: str
    ) -> tuple[str, Dict[str, Any]]:
        """
        * extract content and metadata from different file types
        """
        if content_type == "text/plain":
            return await self._extract_text_content(file_path)
        elif content_type == "application/pdf":
            return await self._extract_pdf_content(file_path)
        elif (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return await self._extract_docx_content(file_path)
        else:
            raise ValueError(f"Unsupported file type: {content_type}")

    async def _extract_pdf_content(self, file_path: str) -> List[Document]:
        """
        * extract content from pdf with page information
        """
        loader = PyPDFLoader(file_path)
        return loader.load()

    async def _extract_docx_content(self, file_path: str) -> List[Document]:
        """
        * extract content from docx with structure information
        """
        loader = UnstructuredWordDocumentLoader(file_path, mode="paged")
        return loader.load()

    async def _extract_text_content(self, file_path: str) -> List[Document]:
        """
        * extract content from plain text files
        """
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()

    def _clean_content(self, text: str):
        # * remove leading and trailing quotes
        cleaned = text.strip("'\"")
        # * normalize whitespace and line breaks
        cleaned = re.sub(r"\s+", " ", cleaned)
        # * remove leading/trailing whitespace
        cleaned = cleaned.strip()
        # * normalize bullet points and numbering - add line breaks before numbered items
        cleaned = re.sub(r"(\d+\.\s*)", r"\n\1", cleaned)
        # * fix spacing around punctuation
        cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
        # * ensure proper spacing after sentences
        cleaned = re.sub(r"([.!?])([^\s])", r"\1 \2", cleaned)
        # * clean up multiple consecutive spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        # * remove extra whitespace around line breaks
        cleaned = re.sub(r"\n\s+", "\n", cleaned)
        cleaned = re.sub(r"\s+\n", "\n", cleaned)
        return cleaned.strip()

    async def _create_chunks(
        self, documents: List[Document], content_type: str
    ) -> List[ChunkMetadata]:
        """
        Create document chunks with enhanced metadata
        - "documents" is the Document objects from single file only
        - So, we can directly identify chunk_index through each chunks
        """
        chunks = []
        chunk_docs = self.text_splitter.split_documents(documents)

        for i, chunk_doc in enumerate(chunk_docs):
            # metadata
            metadata = chunk_doc.metadata
            source = metadata.get("source")
            content = chunk_doc.page_content

            # clean text data
            cleaned_content = self._clean_content(content)

            # * determine page number and section from content
            page_number = self._extract_page_number(chunk_doc, content_type)

            chunk = ChunkMetadata(
                document=cleaned_content,
                source=source,
                filename=os.path.basename(source),
                page_number=page_number,
                chunk_index=i,
            )

            chunks.append(chunk)

        return chunks

    def _extract_page_number(self, doc: Document, content_type: str) -> Optional[int]:
        """
        * extract page number based on file type and metadata keys
        """
        doc_metadata = doc.metadata

        # * check if page metadata exists
        if "page_label" in doc_metadata or "page_number" in doc_metadata:
            if content_type == "application/pdf":
                return doc_metadata.get("page_label", 1)
            elif (
                content_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return doc_metadata.get("page_number", 1)

        # * text files don't have page numbers
        if content_type == "text/plain":
            return None

        # * default for single page documents
        return 1
