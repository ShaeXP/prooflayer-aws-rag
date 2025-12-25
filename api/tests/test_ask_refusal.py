"""Tests for /ask refusal logic."""

import os
from unittest.mock import MagicMock, patch

import pytest

from api.rag import answer_question


@patch("api.rag.search_similar_chunks")
@patch("api.rag.get_embedding")
def test_refusal_no_chunks(mock_get_embedding, mock_search_chunks):
    """Test refusal when no chunks are found."""
    mock_get_embedding.return_value = [0.1] * 1536
    mock_search_chunks.return_value = []
    
    with patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "0.7"}):
        result = answer_question("What is AI?")
    
    assert result["refused"] is True
    assert "No relevant chunks" in result["refusal_reason"]
    assert result["answer"] == ""
    assert result["citations"] == []


@patch("api.rag.search_similar_chunks")
@patch("api.rag.get_embedding")
def test_refusal_low_similarity(mock_get_embedding, mock_search_chunks):
    """Test refusal when similarity is below threshold."""
    mock_get_embedding.return_value = [0.1] * 1536
    mock_search_chunks.return_value = [
        {
            "chunk_id": "chunk1",
            "doc_id": "doc1",
            "content": "Some content",
            "trace_id": "trace1",
            "chunk_index": 0,
            "similarity": 0.5,  # Below threshold of 0.7
        }
    ]
    
    with patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "0.7"}):
        result = answer_question("What is AI?")
    
    assert result["refused"] is True
    assert "below threshold" in result["refusal_reason"]
    assert result["answer"] == ""
    assert result["citations"] == []


@patch("api.rag.search_similar_chunks")
@patch("api.rag.get_embedding")
def test_success_above_threshold(mock_get_embedding, mock_search_chunks):
    """Test successful answer when similarity is above threshold."""
    mock_get_embedding.return_value = [0.1] * 1536
    mock_search_chunks.return_value = [
        {
            "chunk_id": "chunk1",
            "doc_id": "doc1",
            "content": "Artificial intelligence is a field of computer science.",
            "trace_id": "trace1",
            "chunk_index": 0,
            "similarity": 0.85,  # Above threshold
        }
    ]
    
    with patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "0.7"}):
        result = answer_question("What is AI?")
    
    assert result["refused"] is False
    assert result["refusal_reason"] is None
    assert len(result["answer"]) > 0
    assert len(result["citations"]) == 1
    assert result["citations"][0]["score"] == 0.85

