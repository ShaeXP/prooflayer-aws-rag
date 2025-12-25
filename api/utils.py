"""Utility functions for the API."""

import os
import uuid
from datetime import datetime
from pathlib import Path


def generate_trace_id() -> str:
    """Generate a short UUID trace ID."""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for S3 key."""
    # Remove path components and keep only the filename
    path = Path(filename)
    safe_name = path.name
    
    # Replace unsafe characters
    safe_name = safe_name.replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "document.txt"
    
    return safe_name


def build_s3_key(trace_id: str, filename: str) -> str:
    """Build S3 key with trace_id in path."""
    now = datetime.utcnow()
    sanitized = sanitize_filename(filename)
    return f"uploads/{now.year}/{now.month:02d}/{now.day:02d}/{trace_id}/{sanitized}"


def get_env_var(key: str, default: str | None = None) -> str:
    """Get environment variable or raise if missing."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is required")
    return value

