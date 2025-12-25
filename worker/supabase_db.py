"""Supabase Postgres database operations for worker using REST API."""

import json
import os
import urllib.error
import urllib.request
import uuid
from typing import List


def _get_supabase_base_url() -> str:
    """Get Supabase REST API base URL from SUPABASE_URL env var."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise ValueError("SUPABASE_URL is required")
    
    # If it's already a REST API URL, use it directly
    if url.startswith("https://") and "/rest/v1" in url:
        return url.rsplit("/rest/v1", 1)[0] + "/rest/v1"
    
    # If it's a Supabase project URL, convert to REST API URL
    if url.startswith("https://"):
        # Extract project ref from URL like https://xxx.supabase.co
        parts = url.replace("https://", "").replace("http://", "").split(".")
        project_ref = parts[0] if parts else None
        if not project_ref:
            raise ValueError("Could not extract project ref from SUPABASE_URL")
        return f"https://{project_ref}.supabase.co/rest/v1"
    
    raise ValueError(f"Invalid SUPABASE_URL format: {url}. Expected https://xxx.supabase.co")


def _get_headers() -> dict:
    """Get HTTP headers for Supabase REST API requests."""
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
    
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _make_request(method: str, url: str, data: dict | list | None = None) -> dict | list:
    """Make HTTP request to Supabase REST API."""
    headers = _get_headers()
    
    req_data = None
    if data:
        req_data = json.dumps(data).encode("utf-8")
    
    request = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            if response_data:
                return json.loads(response_data)
            return {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise ValueError(f"Supabase API error ({e.code}): {error_body}") from e


def insert_document(
    trace_id: str,
    source_bucket: str,
    source_key: str,
    filename: str,
) -> str:
    """
    Insert a document record and return document ID.
    
    Returns:
        document_id (UUID string)
    """
    base_url = _get_supabase_base_url()
    url = f"{base_url}/documents"
    
    doc_id = str(uuid.uuid4())
    data = {
        "id": doc_id,
        "trace_id": trace_id,
        "source_bucket": source_bucket,
        "source_key": source_key,
        "filename": filename,
    }
    
    response = _make_request("POST", url, data)
    
    # Response should be a list with one item (due to return=representation)
    if isinstance(response, list) and len(response) > 0:
        return str(response[0]["id"])
    elif isinstance(response, dict) and "id" in response:
        return str(response["id"])
    else:
        # Fallback to the ID we generated
        return doc_id


def insert_chunks(
    document_id: str,
    trace_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
) -> None:
    """
    Insert chunks with embeddings via bulk insert.
    
    Args:
        document_id: Parent document ID
        trace_id: Trace ID for the job
        chunks: List of chunk text
        embeddings: List of embedding vectors (same length as chunks)
    """
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have same length")
    
    base_url = _get_supabase_base_url()
    url = f"{base_url}/chunks"
    
    # Prepare bulk insert data
    # For pgvector, PostgREST accepts JSON array format directly
    bulk_data = []
    for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = str(uuid.uuid4())
        # Send embedding as JSON array - PostgREST will convert to vector type
        # Format: [0.1, 0.2, 0.3, ...] as a JSON array
        bulk_data.append({
            "id": chunk_id,
            "document_id": document_id,
            "trace_id": trace_id,
            "chunk_index": idx,
            "content": chunk_text,
            "embedding": embedding,  # Send as JSON array, PostgREST handles conversion
        })
    
    # Bulk insert all chunks at once
    _make_request("POST", url, bulk_data)

