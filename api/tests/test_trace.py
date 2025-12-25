"""Tests for trace ID generation and propagation."""

import re
import uuid

import pytest

from api.utils import build_s3_key, generate_trace_id, sanitize_filename


def test_trace_id_format():
    """Test that trace_id is a valid UUID."""
    trace_id = generate_trace_id()
    
    # Should be a valid UUID
    uuid_obj = uuid.UUID(trace_id)
    assert str(uuid_obj) == trace_id


def test_trace_id_uniqueness():
    """Test that trace_ids are unique."""
    ids = {generate_trace_id() for _ in range(100)}
    assert len(ids) == 100


def test_s3_key_contains_trace_id():
    """Test that S3 key includes trace_id in path."""
    trace_id = generate_trace_id()
    filename = "test.txt"
    key = build_s3_key(trace_id, filename)
    
    # Should contain trace_id
    assert trace_id in key
    
    # Should follow pattern: uploads/YYYY/MM/DD/{trace_id}/filename
    pattern = r"uploads/\d{4}/\d{2}/\d{2}/[a-f0-9-]{36}/test\.txt"
    assert re.match(pattern, key) is not None


def test_sanitize_filename():
    """Test filename sanitization."""
    assert sanitize_filename("test.txt") == "test.txt"
    assert sanitize_filename("test file.txt") == "test_file.txt"
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("file with spaces & special chars!.txt") == "file_with_spaces__special_chars_.txt"

