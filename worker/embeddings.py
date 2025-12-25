"""Embedding generation with pluggable providers."""

import hashlib
import json
import os
import urllib.error
import urllib.request
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


def get_openai_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Generate embedding using OpenAI API via raw HTTPS (stdlib only)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
    
    # Prepare request
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": model,
        "input": text,
    }).encode("utf-8")
    
    # Make HTTPS request
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(request) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            
            # Extract embedding from response
            if "data" in response_data and len(response_data["data"]) > 0:
                embedding = response_data["data"][0]["embedding"]
                if isinstance(embedding, list):
                    return [float(x) for x in embedding]
                else:
                    raise ValueError(f"Unexpected embedding format: {type(embedding)}")
            else:
                raise ValueError(f"Invalid response format: {response_data}")
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get("error", {}).get("message", error_body)
        except Exception:
            error_msg = error_body
        raise ValueError(f"OpenAI API error ({e.code}): {error_msg}") from e
    except Exception as e:
        raise ValueError(f"Error generating OpenAI embedding: {e}") from e


def get_embedding(text: str) -> List[float]:
    """
    Get embedding for text based on EMBEDDING_MODE env var.
    
    Modes:
    - 'fake': Deterministic hash-based embedding (default, 1536 dimensions)
    - 'openai': OpenAI text-embedding-3-small (1536 dimensions, uses raw HTTPS)
    """
    mode = os.getenv("EMBEDDING_MODE", "fake").lower()
    
    if mode == "openai":
        return get_openai_embedding(text)
    else:
        return get_fake_embedding(text)

