from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProcessedDocument(BaseModel):
    id: Optional[str] = None
    filename: str
    chunks_created: int
    content_type: str
    created_at: datetime = Field(default_factory=datetime.now)


class ChunkMetadata(BaseModel):
    document: str
    source: str
    filename: str
    page_number: Optional[int]
    chunk_index: int
    created_at: datetime = Field(default_factory=datetime.now)
