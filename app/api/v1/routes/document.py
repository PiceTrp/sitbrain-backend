import os
import tempfile
from pathlib import Path
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.document_service import DocumentService
from app.utils.logger import LOGGER

router = APIRouter(prefix="/documents", tags=["documents"])


# * dependency injection - create document service directly
def get_document_service() -> DocumentService:
    """
    * create document service instance (uses service_manager internally)
    """
    return DocumentService()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    * upload document and store in qdrant vector database
    """
    try:
        # * validate file type
        allowed_types = [
            "text/plain",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"unsupported file type: {file.content_type}",
            )

        # * validate file size
        # if hasattr(settings, 'max_file_size') and file.size > settings.max_file_size:
        #     raise HTTPException(
        #         status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        #         detail=f"file size exceeds maximum allowed size"
        #     )

        # * create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            temp_path = temp_file.name

            async with aiofiles.open(temp_path, "wb") as f:
                content = await file.read()
                await f.write(content)

        try:
            # * process document and store in qdrant
            processed_doc = await document_service.process_document(
                file_path=temp_path,
                filename=file.filename,
                content_type=file.content_type,
            )

            if processed_doc is None:
                LOGGER.error(f"Processing returned None for file: {file.filename}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Document could not be processed",
                )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "status": "success",
                    "message": "document uploaded and processed successfully",
                    "data": {
                        "filename": processed_doc.filename,
                        "chunks_created": processed_doc.chunks_created,
                        "content_type": processed_doc.content_type,
                        "processed_at": (
                            processed_doc.created_at.isoformat()
                            if hasattr(processed_doc, "created_at")
                            else None
                        ),
                    },
                },
            )

        finally:
            # * cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"document upload failed: {file.filename} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="document processing failed",
        )


@router.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    * upload multiple documents and store in qdrant vector database
    """
    try:
        # * validate number of files
        max_files = getattr(settings, "max_bulk_upload_count", 10)
        if len(files) > max_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"too many files. maximum allowed: {max_files}",
            )

        results = []
        errors = []
        allowed_types = [
            "text/plain",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

        for file in files:
            try:
                # * validate file type
                if file.content_type not in allowed_types:
                    errors.append(
                        {
                            "filename": file.filename,
                            "error": f"unsupported file type: {file.content_type}",
                        }
                    )
                    continue

                # * validate file size
                if (
                    hasattr(settings, "max_file_size")
                    and file.size > settings.max_file_size
                ):
                    errors.append(
                        {
                            "filename": file.filename,
                            "error": "file size exceeds maximum allowed size",
                        }
                    )
                    continue

                # * create temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=Path(file.filename).suffix
                ) as temp_file:
                    temp_path = temp_file.name

                    async with aiofiles.open(temp_path, "wb") as f:
                        content = await file.read()
                        await f.write(content)

                try:
                    # * process document and store in qdrant
                    processed_doc = await document_service.process_document(
                        file_path=temp_path,
                        filename=file.filename,
                        content_type=file.content_type,
                    )

                    results.append(
                        {
                            "filename": file.filename,
                            "chunks_created": processed_doc.chunks_created,
                            "content_type": processed_doc.content_type,
                            "status": "success",
                        }
                    )

                finally:
                    # * cleanup temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

            except Exception as e:
                LOGGER.error(f"file processing failed - {file.filename} - {str(e)}")
                errors.append({"filename": file.filename, "error": str(e)})

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "completed",
                "message": f"processed {len(results)} documents successfully, {len(errors)} failed",
                "data": {
                    "successful": results,
                    "failed": errors,
                    "summary": {
                        "total_files": len(files),
                        "successful_count": len(results),
                        "failed_count": len(errors),
                    },
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"multiple upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="multiple document processing failed",
        )


# # ========================================================================================================

# # @router.get("/{document_id}", response_model=DocumentResponse)
# # async def get_document(document_id: int, db: Session = Depends(get_db)):
# #     """get document by id"""
# #     document = document_service.get_document(db, document_id)
# #     if not document:
# #         raise HTTPException(status_code=404, detail="Document not found")
# #     return document


# # @router.get("/", response_model=List[DocumentResponse])
# # async def get_documents(
# #     skip: int = 0,
# #     limit: int = 100,
# #     db: Session = Depends(get_db)
# # ):
# #     """get all documents with pagination"""
# #     documents = document_service.get_documents(db, skip, limit)
# #     return documents


# # @router.put("/{document_id}", response_model=DocumentResponse)
# # async def update_document(
# #     document_id: int,
# #     document_update: DocumentUpdate,
# #     db: Session = Depends(get_db)
# # ):
# #     """update document metadata and vector embedding"""
# #     try:
# #         db_document = document_service.update_document(db, document_id, document_update)
# #         if not db_document:
# #             raise HTTPException(status_code=404, detail="Document not found")
# #         return db_document
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))


# # @router.delete("/{document_id}", response_model=MessageResponse)
# # async def delete_document(document_id: int, db: Session = Depends(get_db)):
# #     """delete document from both postgresql and vector store"""
# #     try:
# #         success = document_service.delete_document(db, document_id)
# #         if not success:
# #             raise HTTPException(status_code=404, detail="Document not found")
# #         return MessageResponse(message="Document deleted successfully", success=True)
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
