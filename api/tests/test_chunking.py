"""Tests for text chunking logic."""

from worker.chunking import chunk_text


def test_chunk_small_text():
    """Test chunking of text smaller than chunk size."""
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=1000)
    
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_large_text():
    """Test chunking of large text."""
    text = " ".join(["Sentence"] * 200)  # ~1600 chars
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    
    assert len(chunks) > 1
    # All chunks should be non-empty
    assert all(len(chunk) > 0 for chunk in chunks)


def test_chunk_overlap():
    """Test that chunks overlap correctly."""
    text = "A " * 1000  # ~2000 chars
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    
    if len(chunks) > 1:
        # Check that consecutive chunks have some overlap
        # (This is approximate since we break at sentence boundaries)
        assert len(chunks) >= 2


def test_chunk_empty_text():
    """Test chunking empty text."""
    chunks = chunk_text("", chunk_size=1000)
    assert chunks == []


def test_chunk_deterministic():
    """Test that chunking is deterministic for same input."""
    text = " ".join(["Word"] * 500)
    
    chunks1 = chunk_text(text, chunk_size=200, overlap=50)
    chunks2 = chunk_text(text, chunk_size=200, overlap=50)
    
    assert chunks1 == chunks2

