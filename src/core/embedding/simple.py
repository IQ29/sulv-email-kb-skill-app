"""
Simple embedding module with automatic fallback.
Works with Python 3.14 and doesn't require numpy or sentence-transformers.
"""

import logging
import hashlib
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SimpleEmbedding:
    """Simple embedding model that works without external dependencies."""
    
    def __init__(self, model_name: str = "simple-embedding", dimension: int = 128, cache_dir: Optional[str] = None):
        self.model_name = model_name
        self.dimension = dimension
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/embeddings_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "simple_embeddings.json"
        self.embedding_cache: Dict[str, List[float]] = self._load_cache()
        
        logger.info(f"Initialized simple embedding with {dimension} dimensions")
    
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
    
    def _create_simple_embedding(self, text: str) -> List[float]:
        """
        Create a simple embedding based on character n-grams.
        This provides some semantic consistency for similar texts.
        """
        # Convert text to lowercase and clean
        text = text.lower().strip()
        
        # Create character 3-grams
        n = 3
        ngrams = []
        for i in range(len(text) - n + 1):
            ngrams.append(text[i:i+n])
        
        # Create vector based on n-gram hashes
        vector = [0.0] * self.dimension
        
        for ngram in ngrams:
            # Use ngram hash to determine vector positions
            ngram_hash = hash(ngram) % self.dimension
            vector[ngram_hash] += 1.0
        
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
            batch_size: Ignored for simple embedding
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
                embedding = self._create_simple_embedding(text)
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
            "type": "simple",
            "description": "Simple character n-gram embedding (no external dependencies)",
            "cache_size": len(self.embedding_cache),
            "note": "Works with Python 3.14+. For better semantic embeddings, use MiniLM with Python 3.13 or earlier."
        }


class SimpleEmbeddingFactory:
    """Factory for simple embedding models."""
    
    @staticmethod
    def create_model(model_type: str = "simple", **kwargs) -> SimpleEmbedding:
        """
        Create a simple embedding model.
        
        Args:
            model_type: Always "simple" for this factory
            **kwargs: Model parameters
            
        Returns:
            SimpleEmbedding instance
        """
        return SimpleEmbedding(**kwargs)
    
    @staticmethod
    def get_model_info(model_type: str) -> dict:
        """Get information about embedding models."""
        return {
            "simple": {
                "name": "simple-embedding",
                "size_mb": 0,
                "dimension": 128,
                "best_for": "Basic functionality without dependencies",
                "pros": "Works with Python 3.14+, no external dependencies",
                "cons": "Not semantically meaningful, basic similarity only"
            }
        }


# Test the simple embedding
if __name__ == "__main__":
    print("Testing simple embedding...")
    
    embedder = SimpleEmbeddingFactory.create_model()
    
    texts = [
        "SULV Construction project in St Ives",
        "Building a duplex for client Yvette",
        "Construction project management"
    ]
    
    embeddings = embedder.embed(texts)
    
    print(f"Created {len(embeddings)} embeddings")
    print(f"Each embedding has {len(embeddings[0])} dimensions")
    print(f"Model info: {embedder.get_info()['description']}")
    
    # Test similarity
    if len(embeddings) >= 2:
        # Simple cosine similarity
        vec1 = embeddings[0]
        vec2 = embeddings[1]
        similarity = sum(a * b for a, b in zip(vec1, vec2))
        print(f"Similarity between text 1 and 2: {similarity:.3f}")