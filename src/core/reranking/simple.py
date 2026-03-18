"""
Simple reranking module that works without external dependencies.
Uses basic text similarity metrics.
"""

import logging
from typing import List, Tuple, Dict, Any
import re

logger = logging.getLogger(__name__)


class SimpleReranker:
    """Simple reranker using basic text similarity."""
    
    def __init__(self, model_name: str = "simple-reranker"):
        self.model_name = model_name
    
    def rerank(self, query: str, documents: List[str], **kwargs) -> List[Tuple[int, float]]:
        """
        Rerank documents based on similarity to query.
        
        Args:
            query: Search query
            documents: List of document texts to rerank
            **kwargs: Additional parameters
            
        Returns:
            List of (index, score) pairs sorted by score (descending)
        """
        if not documents:
            return []
        
        scores = []
        query_terms = self._extract_terms(query)
        
        for i, doc in enumerate(documents):
            doc_terms = self._extract_terms(doc)
            score = self._calculate_similarity(query_terms, doc_terms)
            scores.append((i, score))
        
        # Sort by score (descending)
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def _extract_terms(self, text: str) -> Dict[str, float]:
        """Extract terms from text with weights."""
        # Convert to lowercase and split
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Count term frequencies
        term_counts = {}
        for word in words:
            if len(word) > 2:  # Ignore very short words
                term_counts[word] = term_counts.get(word, 0) + 1
        
        # Calculate TF (term frequency) weights
        total_terms = len(words)
        if total_terms == 0:
            return {}
        
        term_weights = {}
        for term, count in term_counts.items():
            term_weights[term] = count / total_terms
        
        return term_weights
    
    def _calculate_similarity(self, query_terms: Dict[str, float], doc_terms: Dict[str, float]) -> float:
        """Calculate similarity between query and document terms."""
        if not query_terms or not doc_terms:
            return 0.0
        
        # Calculate dot product (cosine similarity simplified)
        similarity = 0.0
        for term, q_weight in query_terms.items():
            if term in doc_terms:
                similarity += q_weight * doc_terms[term]
        
        # Normalize by query length
        query_norm = sum(w * w for w in query_terms.values()) ** 0.5
        if query_norm > 0:
            similarity /= query_norm
        
        return similarity
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the reranker."""
        return {
            "model_name": self.model_name,
            "type": "simple",
            "description": "Simple term frequency reranker (no external dependencies)",
            "note": "Works with Python 3.14+. For better reranking, use cross-encoder with Python 3.13 or earlier."
        }


class SimpleRerankingFactory:
    """Factory for simple reranking models."""
    
    @staticmethod
    def create_reranker(reranker_type: str = "simple", **kwargs) -> SimpleReranker:
        """
        Create a simple reranker.
        
        Args:
            reranker_type: Always "simple" for this factory
            **kwargs: Model parameters
            
        Returns:
            SimpleReranker instance
        """
        return SimpleReranker(**kwargs)
    
    @staticmethod
    def get_reranker_info(reranker_type: str) -> dict:
        """Get information about reranking models."""
        return {
            "simple": {
                "name": "simple-reranker",
                "accuracy": "basic",
                "speed": "fast",
                "best_for": "Basic reranking without dependencies",
                "pros": "Works with Python 3.14+, no external dependencies",
                "cons": "Basic term matching only"
            }
        }


# Test the simple reranking
if __name__ == "__main__":
    print("Testing simple reranking...")
    
    reranker = SimpleRerankingFactory.create_reranker()
    
    query = "SULV Construction duplex project in St Ives"
    
    documents = [
        "SULV is building a duplex in St Ives for client Yvette.",
        "Construction project management for residential buildings.",
        "St Ives is a suburb in northern Sydney with good schools.",
        "The duplex project includes sustainable features like solar panels."
    ]
    
    results = reranker.rerank(query, documents)
    
    print(f"Reranked {len(documents)} documents")
    print("\nTop results:")
    for rank, (idx, score) in enumerate(results[:3], 1):
        print(f"  Rank {rank}: Score {score:.3f}")
        print(f"     {documents[idx][:60]}...")