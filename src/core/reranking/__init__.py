"""
Reranking models for improving search results.
Automatically uses simple reranker for Python 3.14 compatibility.
"""

import logging
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class Reranker:
    """Base class for reranking models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def rerank(self, query: str, documents: List[str], **kwargs) -> List[Tuple[int, float]]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of document texts to rerank
            **kwargs: Additional parameters
            
        Returns:
            List of (index, score) pairs sorted by score (descending)
        """
        raise NotImplementedError


class SimpleRerankerWrapper(Reranker):
    """Wrapper for simple reranker (works with Python 3.14)."""
    
    def __init__(self, model_name: str = "simple"):
        super().__init__(model_name)
        from .simple import SimpleReranker
        self.model = SimpleReranker(model_name=model_name)
    
    def rerank(self, query: str, documents: List[str], **kwargs) -> List[Tuple[int, float]]:
        """Rerank documents using simple model."""
        return self.model.rerank(query, documents, **kwargs)
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return self.model.get_info()


class RerankingFactory:
    """Factory to create reranking models with automatic fallback."""
    
    @staticmethod
    def create_reranker(reranker_type: str = "simple", **kwargs) -> Reranker:
        """
        Create a reranker with automatic fallback.
        
        Args:
            reranker_type: One of "cross-encoder", "bge", "colbert", "simple"
            **kwargs: Model-specific parameters
            
        Returns:
            Reranker instance
        """
        # For Python 3.14 compatibility, always use simple reranker
        # Other models require Python 3.13 or earlier
        logger.info(f"Using simple reranker for Python 3.14 compatibility")
        logger.info(f"Note: For cross-encoder/BGE reranking, use Python 3.13 or earlier")
        
        return SimpleRerankerWrapper(reranker_type)
    
    @staticmethod
    def get_reranker_info(reranker_type: str) -> dict:
        """Get information about reranking models."""
        rerankers = {
            "simple": {
                "name": "simple-reranker",
                "accuracy": "basic",
                "speed": "fast",
                "best_for": "Basic reranking without dependencies",
                "pros": "Works with Python 3.14+, no external dependencies",
                "cons": "Basic term matching only",
                "python_version": "3.14+"
            },
            "cross-encoder": {
                "name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "size_mb": 80,
                "accuracy": "high",
                "speed": "medium",
                "best_for": "General reranking, high accuracy",
                "pros": "Accurate, easy to use",
                "cons": "Requires Python 3.13 or earlier",
                "python_version": "≤3.13"
            },
            "bge": {
                "name": "BAAI/bge-reranker-base",
                "size_mb": 400,
                "accuracy": "very high",
                "speed": "medium",
                "best_for": "Retrieval-focused reranking",
                "pros": "State-of-the-art for retrieval",
                "cons": "Requires Python 3.13 or earlier",
                "python_version": "≤3.13"
            },
            "colbert": {
                "name": "colbert-ir/colbertv2.0",
                "size_mb": 1100,
                "accuracy": "excellent",
                "speed": "slow",
                "best_for": "Maximum accuracy, academic use",
                "pros": "Very accurate, late interaction",
                "cons": "Requires Python 3.13 or earlier",
                "python_version": "≤3.13"
            }
        }
        
        return rerankers.get(reranker_type, {})


# Test the reranking module
if __name__ == "__main__":
    print("Testing reranking module (Python 3.14 compatible)...")
    
    query = "SULV Construction duplex project in St Ives"
    
    documents = [
        "SULV is building a duplex in St Ives for client Yvette.",
        "Construction project management for residential buildings.",
        "St Ives is a suburb in northern Sydney with good schools.",
        "The duplex project includes sustainable features like solar panels."
    ]
    
    # Test simple reranker
    print("\n1. Simple reranking:")
    try:
        reranker = RerankingFactory.create_reranker("simple")
        results = reranker.rerank(query, documents)
        
        print(f"  Reranked {len(documents)} documents")
        for rank, (idx, score) in enumerate(results[:3], 1):
            print(f"  Rank {rank}: Score {score:.3f} - {documents[idx][:50]}...")
    except Exception as e:
        print(f"  ❌ Simple reranker failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Show model info
    print("\n2. Available rerankers:")
    for reranker_type in ["simple", "cross-encoder", "bge", "colbert"]:
        info = RerankingFactory.get_reranker_info(reranker_type)
        print(f"  {reranker_type}: {info.get('accuracy', 'N/A')} accuracy ({info.get('python_version', 'N/A')})")