"""
Fallback embedding implementation for when sentence-transformers is not available.
Uses simple TF-IDF like embeddings for basic functionality.
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FallbackEmbedding:
    """Fallback embedding using simple word frequency vectors."""
    
    def __init__(self, model_name: str = "fallback-tfidf", cache_dir: Optional[str] = None):
        self.model_name = model_name
        self.dimension = 128  # Fixed dimension for fallback
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/embeddings_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "fallback_embeddings.json"
        self.embedding_cache: Dict[str, List[float]] = self._load_cache()
        
        logger.info(f"Initialized fallback embedding with {self.dimension} dimensions")
    
    def _load_cache(self) -> Dict[str, List[float]]:
        """Load embedding cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save embedding cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.embedding_cache, f)
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    def _text_to_hash(self, text: str) -> str:
        """Create a hash for text caching."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _create_fallback_embedding(self, text: str) -> List[float]:
        """
        Create a simple embedding based on word frequencies.
        This is a very basic fallback - not semantically meaningful,
        but consistent for the same text.
        """
        # Simple algorithm: hash each word and create vector
        words = text.lower().split()
        vector = [0.0] * self.dimension
        
        for word in words:
            # Use word hash to determine vector positions
            word_hash = hash(word) % self.dimension
            vector[word_hash] += 1.0
        
        # Normalize the vector
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    def embed(self, texts: List[str], batch_size: int = 32, **kwargs) -> List[List[float]]:
        """
        Create embeddings for texts.
        
        Args:
            texts: List of text strings
            batch_size: Ignored for fallback
            **kwargs: Additional parameters
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            text_hash = self._text_to_hash(text)
            
            # Check cache first
            if text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
            else:
                # Create new embedding
                embedding = self._create_fallback_embedding(text)
                self.embedding_cache[text_hash] = embedding
                embeddings.append(embedding)
        
        # Save cache periodically
        if len(self.embedding_cache) % 100 == 0:
            self._save_cache()
        
        return embeddings
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "type": "fallback",
            "description": "Simple word frequency fallback embedding",
            "cache_size": len(self.embedding_cache),
            "note": "This is a fallback implementation. For semantic embeddings, use MiniLM with Python 3.13 or earlier."
        }


class FallbackEmbeddingFactory:
    """Factory for fallback embedding models."""
    
    @staticmethod
    def create_model(model_type: str = "fallback", **kwargs) -> FallbackEmbedding:
        """
        Create a fallback embedding model.
        
        Args:
            model_type: Always "fallback" for this factory
            **kwargs: Model parameters
            
        Returns:
            FallbackEmbedding instance
        """
        return FallbackEmbedding(**kwargs)


# Test the fallback embedding
if __name__ == "__main__":
    print("Testing fallback embedding...")
    
    embedder = FallbackEmbedding()
    
    texts = [
        "SULV Construction project in St Ives",
        "Building a duplex for client Yvette",
        "Construction project management"
    ]
    
    embeddings = embedder.embed(texts)
    
    print(f"Created {len(embeddings)} embeddings")
    print(f"Each embedding has {len(embeddings[0])} dimensions")
    print(f"Model info: {embedder.get_info()['description']}")