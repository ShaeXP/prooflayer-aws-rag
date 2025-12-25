"""Supabase Postgres database operations for worker."""

import os
import uuid
from typing import List

import psycopg


def get_db_connection():
    """Get database connection from Supabase.
    
    Expects SUPABASE_URL to be either:
    - A direct postgresql:// connection string, OR
    - A Supabase project URL (https://xxx.supabase.co) which will be converted
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url:
        raise ValueError("SUPABASE_URL is required")
    
    # If it's already a postgres URL, use it directly
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return psycopg.connect(url)
    
    # Otherwise, construct from Supabase project URL
    if url.startswith("https://"):
        if not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required when using Supabase project URL")
        
        # Extract project ref from URL like https://xxx.supabase.co
        parts = url.replace("https://", "").replace("http://", "").split(".")
        project_ref = parts[0] if parts else None
        if not project_ref:
            raise ValueError("Could not extract project ref from SUPABASE_URL")
        
        # Use direct connection (port 5432) or pooler (port 6543)
        # Direct connection is more reliable for serverless
        region = os.getenv("AWS_REGION", "us-east-1")
        db_url = f"postgresql://postgres.{project_ref}:{key}@aws-0-{region}.pooler.supabase.com:6543/postgres"
        return psycopg.connect(db_url)
    
    raise ValueError(f"Invalid SUPABASE_URL format: {url}")


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
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            doc_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO documents (id, trace_id, source_bucket, source_key, filename)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (doc_id, trace_id, source_bucket, source_key, filename),
            )
            conn.commit()
            return doc_id
    finally:
        conn.close()


def insert_chunks(
    document_id: str,
    trace_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
) -> None:
    """
    Insert chunks with embeddings.
    
    Args:
        document_id: Parent document ID
        trace_id: Trace ID for the job
        chunks: List of chunk text
        embeddings: List of embedding vectors (same length as chunks)
    """
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have same length")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                # Convert embedding list to pgvector format string
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
                
                cur.execute(
                    """
                    INSERT INTO chunks (id, document_id, trace_id, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
                    """,
                    (chunk_id, document_id, trace_id, idx, chunk_text, embedding_str),
                )
            conn.commit()
    finally:
        conn.close()

