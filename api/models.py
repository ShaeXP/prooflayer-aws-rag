"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    """Request for presigned S3 URL."""

    filename: str = Field(..., description="Filename to upload")


class PresignResponse(BaseModel):
    """Response with presigned S3 URL."""

    trace_id: str
    bucket: str
    key: str
    url: str


class AskRequest(BaseModel):
    """Request for RAG query."""

    question: str = Field(..., description="Question to answer")
    top_k: int = Field(default=10, ge=1, le=20, description="Number of chunks to retrieve")


class Citation(BaseModel):
    """Citation from retrieved chunk."""

    doc_id: str
    chunk_id: str
    score: float
    excerpt: str


class AskResponse(BaseModel):
    """Response with answer and citations."""

    trace_id: str
    answer: str
    citations: list[Citation]
    refused: bool
    refusal_reason: str | None = None

