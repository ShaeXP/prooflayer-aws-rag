"""Utility functions for the worker."""

import json
import logging
import os
import re
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_trace_id() -> str:
    """Generate a short UUID trace_id."""
    return str(uuid.uuid4())


def extract_trace_id_from_key(s3_key: str) -> str | None:
    """Extract trace_id from S3 key path.
    
    Expected format: uploads/YYYY/MM/DD/{trace_id}/filename
    """
    # Pattern: uploads/YYYY/MM/DD/{uuid}/filename
    pattern = r"uploads/\d{4}/\d{2}/\d{2}/([a-f0-9-]{36})/"
    match = re.search(pattern, s3_key)
    if match:
        return match.group(1)
    return None


def log_structured(level: str, event: str, trace_id: str, **kwargs):
    """Log structured JSON."""
    log_data = {
        "event": event,
        "trace_id": trace_id,
        **kwargs,
    }
    message = json.dumps(log_data)
    
    if level == "info":
        logger.info(message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.debug(message)

