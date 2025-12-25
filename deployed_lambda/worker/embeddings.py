"""Embedding generation with pluggable providers."""

import hashlib
import os
from typing import List


def get_fake_embedding(text: str, dimension: int = 1536) -> List[float]:
    """
    Generate a deterministic fake embedding for testing.
    
    Uses hash-based approach to create a consistent vector.
    """
    # Create hash from text
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Generate vector from hash
    vector = []
    for i in range(dimension):
        # Use different parts of hash to fill vector
        byte_idx = i % len(hash_bytes)
        # Normalize to [-1, 1] range
        value = (hash_bytes[byte_idx] / 255.0) * 2 - 1
        vector.append(value)
    
    return vector


def get_openai_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI API."""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
        
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
        )
        return response.data[0].embedding
    except ImportError:
        raise ValueError("openai package is required for OpenAI embeddings")
    except Exception as e:
        raise ValueError(f"Error generating OpenAI embedding: {e}")


def get_embedding(text: str) -> List[float]:
    """
    Get embedding for text based on EMBEDDING_MODE env var.
    
    Modes:
    - 'fake': Deterministic hash-based embedding (default)
    - 'openai': OpenAI text-embedding-ada-002
    """
    mode = os.getenv("EMBEDDING_MODE", "fake").lower()
    
    if mode == "openai":
        return get_openai_embedding(text)
    else:
        return get_fake_embedding(text)

