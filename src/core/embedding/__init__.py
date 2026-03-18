"""
Embedding models for converting text to vectors.
Automatically uses simple embedding for Python 3.14 compatibility.
"""

import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Base class for embedding models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def embed(self, texts: List[str], batch_size: int = 32, **kwargs) -> List[List[float]]:
        """
        Create embeddings for texts.
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            **kwargs: Additional parameters
            
        Returns:
            List of embedding vectors
        """
        raise NotImplementedError
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "type": "unknown"
        }


class SimpleEmbeddingWrapper(EmbeddingModel):
    """Wrapper for simple embedding (works with Python 3.14)."""
    
    def __init__(self, model_name: str = "simple"):
        super().__init__(model_name)
        from .simple import SimpleEmbedding
        self.model = SimpleEmbedding(model_name=model_name)
    
    def embed(self, texts: List[str], batch_size: int = 32, **kwargs) -> List[List[float]]:
        """Create embeddings using simple model."""
        return self.model.embed(texts, batch_size=batch_size, **kwargs)
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        info = super().get_info()
        info.update(self.model.get_info())
        return info


class EmbeddingFactory:
    """Factory to create embedding models with automatic fallback."""
    
    @staticmethod
    def create_model(model_type: str = "simple", **kwargs) -> EmbeddingModel:
        """
        Create an embedding model with automatic fallback.
        
        Args:
            model_type: One of "minilm", "bge", "fasttext", "simple"
            **kwargs: Model-specific parameters
            
        Returns:
            EmbeddingModel instance
        """
        # For Python 3.14 compatibility, always use simple embedding
        # Other models require Python 3.13 or earlier
        logger.info(f"Using simple embedding for Python 3.14 compatibility")
        logger.info(f"Note: For MiniLM/BGE/FastText, use Python 3.13 or earlier")
        
        return SimpleEmbeddingWrapper(model_type)
    
    @staticmethod
    def get_model_info(model_type: str) -> dict:
        """Get information about embedding models."""
        models = {
            "simple": {
                "name": "simple-embedding",
                "size_mb": 0,
                "dimension": 128,
                "best_for": "Basic functionality without dependencies",
                "pros": "Works with Python 3.14+, no external dependencies",
                "cons": "Basic similarity only",
                "python_version": "3.14+"
            },
            "minilm": {
                "name": "all-MiniLM-L6-v2",
                "size_mb": 80,
                "dimension": 384,
                "best_for": "General purpose, fast embedding",
                "pros": "Small, fast, good quality",
                "cons": "Requires Python 3.13 or earlier",
                "python_version": "≤3.13"
            },
            "bge": {
                "name": "BAAI/bge-small-en-v1.5",
                "size_mb": 400,
                "dimension": 384,
                "best_for": "Retrieval tasks",
                "pros": "Better for search/retrieval",
                "cons": "Requires Python 3.13 or earlier",
                "python_version": "≤3.13"
            },
            "fasttext": {
                "name": "cc.en.300.bin",
                "size_mb": 1000,
                "dimension": 300,
                "best_for": "Multilingual, OOV words",
                "pros": "Multilingual, handles unknown words",
                "cons": "Requires Python 3.13 or earlier",
                "python_version": "≤3.13"
            }
        }
        
        return models.get(model_type, {})


# Test the embedding module
if __name__ == "__main__":
    print("Testing embedding module (Python 3.14 compatible)...")
    
    # Test simple embedding
    print("\n1. Simple embedding:")
    try:
        embedder = EmbeddingFactory.create_model("simple")
        texts = ["SULV Construction project", "St Ives duplex build"]
        embeddings = embedder.embed(texts)
        
        print(f"  Created {len(embeddings)} embeddings")
        print(f"  Each embedding has {len(embeddings[0])} dimensions")
        print(f"  Model info: {embedder.get_info()['description']}")
    except Exception as e:
        print(f"  ❌ Simple embedding failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Show model info
    print("\n2. Available models:")
    for model_type in ["simple", "minilm", "bge", "fasttext"]:
        info = EmbeddingFactory.get_model_info(model_type)
        print(f"  {model_type}: {info.get('size_mb', 'N/A')}MB, {info.get('dimension', 'N/A')}D ({info.get('python_version', 'N/A')})")