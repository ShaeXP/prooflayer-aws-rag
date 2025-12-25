"""Supabase Postgres database connection and operations."""

import logging
import os
from typing import Any

import psycopg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection from Supabase.
    
    Expects SUPABASE_URL to be either:
    - A direct postgresql:// connection string, OR
    - A Supabase project URL (https://xxx.supabase.co) which will be converted
    
    By default, uses direct connection (db.<project-ref>.supabase.co:5432).
    Set SUPABASE_USE_POOLER=true to use pooler connection.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    use_pooler = os.getenv("SUPABASE_USE_POOLER", "false").lower() == "true"
    debug_rag = os.getenv("DEBUG_RAG", "false").lower() == "true"
    
    if not url:
        raise ValueError("SUPABASE_URL is required")
    
    # Debug logging (safe - no secrets)
    if debug_rag:
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            logger.info("SUPABASE_URL format: postgresql:// connection string")
            try:
                if "@" in url:
                    host_port = url.split("@")[1].split("/")[0]
                    logger.info(f"Supabase connection: {host_port}")
            except Exception:
                pass
        elif url.startswith("https://"):
            logger.info("SUPABASE_URL format: https:// project URL")
            parts = url.replace("https://", "").replace("http://", "").split(".")
            project_ref = parts[0] if parts else None
            if project_ref:
                logger.info(f"Derived project_ref: {project_ref}")
                if use_pooler:
                    region = os.getenv("AWS_REGION", "us-east-1")
                    logger.info(f"Using pooler: aws-0-{region}.pooler.supabase.com:6543")
                else:
                    logger.info(f"Using direct: db.{project_ref}.supabase.co:5432")
    
    # If it's already a postgres URL, use it directly
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        # Extract host/port from connection string for error messages
        try:
            # Parse connection string to show host/port in errors
            if "@" in url and ":" in url:
                parts = url.split("@")
                if len(parts) == 2:
                    host_port = parts[1].split("/")[0]
                    if ":" in host_port:
                        host, port = host_port.split(":", 1)
                        if debug_rag:
                            logger.info(f"Connecting to Supabase: {host}:{port}")
        except Exception:
            pass  # If parsing fails, just try to connect
        try:
            return psycopg.connect(url)
        except Exception as e:
            # Extract host/port for clearer error
            if "@" in url:
                try:
                    host_port = url.split("@")[1].split("/")[0]
                    raise ConnectionError(f"Failed to connect to {host_port}: {e}") from e
                except Exception:
                    pass
            raise
    
    # Otherwise, construct from Supabase project URL
    if url.startswith("https://"):
        if not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required when using Supabase project URL")
        if not db_password:
            raise ValueError("SUPABASE_DB_PASSWORD is required for Postgres connections")
        
        # Extract project ref from URL like https://xxx.supabase.co
        parts = url.replace("https://", "").replace("http://", "").split(".")
        project_ref = parts[0] if parts else None
        if not project_ref:
            raise ValueError("Could not extract project ref from SUPABASE_URL")
        
        # Use direct connection (port 5432) by default, pooler (port 6543) if requested
        if use_pooler:
            region = os.getenv("AWS_REGION", "us-east-1")
            host = f"aws-0-{region}.pooler.supabase.com"
            port = 6543
            # Ensure correct tenant username format for pooler
            username = f"postgres.{project_ref}"
            db_url = f"postgresql://{username}:{db_password}@{host}:{port}/postgres?sslmode=require&connect_timeout=5"
            if debug_rag:
                logger.info(f"Connecting to Supabase pooler: {host}:{port} (username: {username})")
        else:
            # Direct connection - more reliable for local development
            host = f"db.{project_ref}.supabase.co"
            port = 5432
            username = f"postgres.{project_ref}"
            db_url = f"postgresql://{username}:{db_password}@{host}:{port}/postgres?sslmode=require&connect_timeout=5"
            if debug_rag:
                logger.info(f"Connecting to Supabase direct: {host}:{port} (username: {username})")
        
        try:
            return psycopg.connect(db_url)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase {host}:{port}: {e}") from e
    
    raise ValueError(f"Invalid SUPABASE_URL format: {url}. Expected postgresql://... or https://xxx.supabase.co")


def get_table_counts() -> dict[str, int]:
    """Get counts from chunks and documents tables for debugging."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks")
            chunks_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM documents")
            documents_count = cur.fetchone()[0]
            
            return {
                "chunks": chunks_count,
                "documents": documents_count,
            }
    finally:
        conn.close()


def search_similar_chunks(
    question_embedding: list[float],
    top_k: int,
    similarity_threshold: float = 0.48,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Search for similar chunks using pgvector cosine similarity.
    
    Returns:
        (filtered_results, all_results) where:
        - filtered_results: chunks with similarity >= threshold
        - all_results: top_k chunks without threshold (for debugging)
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Convert embedding list to PostgreSQL array format
            embedding_array = "[" + ",".join(str(v) for v in question_embedding) + "]"
            
            # First, fetch top_k chunks WITHOUT threshold (for debugging)
            query_all = """
                SELECT 
                    c.id as chunk_id,
                    c.document_id as doc_id,
                    c.content,
                    c.trace_id,
                    c.chunk_index,
                    1 - (c.embedding <=> %s::vector) as similarity
                FROM chunks c
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
            """
            
            cur.execute(query_all, (embedding_array, embedding_array, top_k))
            
            all_results = []
            for row in cur.fetchall():
                chunk_id, doc_id, content, trace_id, chunk_index, similarity = row
                all_results.append({
                    "chunk_id": str(chunk_id),
                    "doc_id": str(doc_id),
                    "content": content,
                    "trace_id": trace_id,
                    "chunk_index": chunk_index,
                    "similarity": float(similarity),
                })
            
            # Filter by threshold in Python
            filtered_results = [r for r in all_results if r["similarity"] >= similarity_threshold]
            
            return filtered_results, all_results
    finally:
        conn.close()

