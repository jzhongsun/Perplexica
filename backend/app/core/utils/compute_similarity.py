"""Compute similarity between embeddings."""
from typing import List
import numpy as np

def compute_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)) 