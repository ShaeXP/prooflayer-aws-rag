"""RAG (Retrieval Augmented Generation) logic."""

import logging
import os
from typing import Any

from dotenv import load_dotenv

from api.supabase_db import get_table_counts, search_similar_chunks
from api.utils import generate_trace_id
from worker.embeddings import get_embedding

load_dotenv()

logger = logging.getLogger(__name__)


def answer_question(question: str, top_k: int = 10) -> dict[str, Any]:
    """
    Answer a question using RAG.
    
    Returns answer, citations, and refusal status.
    """
    trace_id = generate_trace_id()
    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
    debug_rag = os.getenv("DEBUG_RAG", "false").lower() == "true"
    
    # Generate embedding for question
    embedding_mode = os.getenv("EMBEDDING_MODE", "fake").lower()
    question_embedding = get_embedding(question)
    
    if debug_rag:
        logger.info(f"RAG query: embedding_mode={embedding_mode}, dimension={len(question_embedding)}, threshold={similarity_threshold}")
    
    # Get table counts for debugging
    debug_info = {}
    if debug_rag:
        try:
            counts = get_table_counts()
            debug_info["table_counts"] = counts
            logger.info(f"Database counts: {counts}")
        except Exception as e:
            logger.warning(f"Failed to get table counts: {e}")
            debug_info["table_counts_error"] = str(e)
    
    # Search for similar chunks (returns filtered and all results)
    filtered_chunks, all_chunks = search_similar_chunks(question_embedding, top_k, similarity_threshold)
    
    # Get best similarity score for logging and refusal logic
    best_similarity = all_chunks[0]["similarity"] if all_chunks else 0.0
    returned_chunk_count = len(filtered_chunks)
    
    # Improved refusal policy with low confidence tier
    # Floor is 0.50 (so low confidence answers are allowed down to 0.50)
    low_confidence_threshold = max(0.45, similarity_threshold - 0.70)
    
    # Log retrieval metrics
    logger.info(
        f"RAG retrieval: top_k={top_k}, similarity_threshold={similarity_threshold:.3f}, "
        f"best_similarity={best_similarity:.3f}, fallback_floor={low_confidence_threshold:.3f}, "
        f"returned_chunks={returned_chunk_count}"
    )
    
    if debug_rag:
        logger.info(f"Retrieved {len(all_chunks)} chunks, {len(filtered_chunks)} passed threshold")
        if all_chunks:
            top_similarities = [{"similarity": c["similarity"], "trace_id": c["trace_id"]} for c in all_chunks[:5]]
            debug_info["top_similarities"] = top_similarities
            logger.info(f"Top similarities: {[s['similarity'] for s in top_similarities]}")
    
    # Check if we have any results
    if not all_chunks:
        # No chunks returned at all
        chunks_count = debug_info.get("table_counts", {}).get("chunks", 0)
        if chunks_count > 0:
            refusal_reason = (
                f"Chunks exist ({chunks_count} total) but query returned no results. "
                f"Possible embedding mismatch or dimension issue."
            )
        else:
            refusal_reason = "No chunks found in knowledge base"
        
        result = {
            "trace_id": trace_id,
            "answer": "",
            "citations": [],
            "refused": True,
            "refusal_reason": refusal_reason,
        }
        if debug_rag:
            result["debug"] = debug_info
        return result
    
    # Determine if we should answer or refuse based on best similarity
    if best_similarity >= similarity_threshold:
        # High confidence: use filtered chunks (above threshold)
        chunks_to_use = filtered_chunks
        low_confidence = False
    elif best_similarity >= low_confidence_threshold:
        # Low confidence: use best chunks even if below threshold
        chunks_to_use = all_chunks[:min(3, len(all_chunks))]  # Use top 3 for low confidence
        low_confidence = True
    else:
        # Too low: refuse
        refusal_reason = (
            f"Best similarity ({best_similarity:.3f}) below low confidence threshold ({low_confidence_threshold:.3f}). "
            f"Similarity threshold is {similarity_threshold:.3f}."
        )
        result = {
            "trace_id": trace_id,
            "answer": "",
            "citations": [],
            "refused": True,
            "refusal_reason": refusal_reason,
        }
        if debug_rag:
            result["debug"] = debug_info
        return result
    
    # Build answer from chunks
    answer_parts = []
    citations = []
    
    for chunk in chunks_to_use:
        excerpt = chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
        citations.append({
            "doc_id": chunk["doc_id"],
            "chunk_id": chunk["chunk_id"],
            "score": chunk["similarity"],
            "excerpt": excerpt,
        })
        answer_parts.append(chunk["content"])
    
    answer = "\n\n".join(answer_parts)
    
    # Add low confidence note if applicable
    if low_confidence:
        answer = f"[Low confidence answer - similarity {best_similarity:.3f} below threshold {similarity_threshold:.3f}]\n\n{answer}"
    
    result = {
        "trace_id": trace_id,
        "answer": answer,
        "citations": citations,
        "refused": False,
        "refusal_reason": None,
    }
    if debug_rag:
        result["debug"] = debug_info
    
    return result

