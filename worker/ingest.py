"""Document ingestion logic."""

import json
import logging
import os

import boto3

from .chunking import chunk_text
from .embeddings import get_embedding
from .supabase_db import insert_chunks, insert_document
from .utils import extract_trace_id_from_key, generate_trace_id, log_structured

logger = logging.getLogger(__name__)


def ingest_document(bucket: str, key: str) -> None:
    """
    Ingest a document from S3: download, chunk, embed, store.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    """
    # Extract or generate trace_id
    trace_id = extract_trace_id_from_key(key)
    if not trace_id:
        trace_id = generate_trace_id()
        log_structured("warning", "trace_id_not_in_key", trace_id, key=key)
    
    log_structured("info", "ingest_started", trace_id, bucket=bucket, key=key)
    
    try:
        # Download from S3
        s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = s3_client.get_object(Bucket=bucket, Key=key)
        text = response["Body"].read().decode("utf-8")
        
        log_structured("info", "document_downloaded", trace_id, size_bytes=len(text))
        
        # Extract filename from key
        filename = key.split("/")[-1]
        
        # Insert document record
        doc_id = insert_document(trace_id, bucket, key, filename)
        log_structured("info", "document_inserted", trace_id, doc_id=doc_id)
        
        # Chunk text
        chunks = chunk_text(text)
        log_structured("info", "text_chunked", trace_id, chunk_count=len(chunks))
        
        # Generate embeddings
        embeddings = []
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            embeddings.append(embedding)
            if (i + 1) % 10 == 0:
                log_structured("info", "embeddings_progress", trace_id, processed=i + 1, total=len(chunks))
        
        log_structured("info", "embeddings_generated", trace_id, count=len(embeddings))
        
        # Insert chunks with embeddings
        insert_chunks(doc_id, trace_id, chunks, embeddings)
        log_structured("info", "chunks_inserted", trace_id, count=len(chunks))
        
        log_structured("info", "ingest_completed", trace_id)
        
    except Exception as e:
        log_structured("error", "ingest_failed", trace_id, error=str(e))
        raise

