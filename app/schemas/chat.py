from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    * chat message schema
    """

    message: str = Field(
        ..., min_length=1, max_length=2000, description="user question"
    )
    session_id: Optional[str] = Field(None, description="optional session identifier")
    include_sources: bool = Field(
        True, description="whether to include source references"
    )


class ChatRequest(BaseModel):
    """
    * chat request schema
    """

    question: str = Field(..., description="question from user")


class ChatResponse(BaseModel):
    """
    * chat response with sources and confidence
    """

    answer: str = Field(..., description="generated answer")
    sources: List[str] = Field(default=[], description="source references")
    processing_time: float = Field(..., description="processing time in seconds")
    session_id: Optional[str] = Field(None, description="session identifier")
