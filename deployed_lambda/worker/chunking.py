"""Text chunking logic."""

from typing import List


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If not the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 200 chars
            for i in range(end, max(start + chunk_size - 200, start), -1):
                if text[i] in ".!?\n":
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start forward with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

