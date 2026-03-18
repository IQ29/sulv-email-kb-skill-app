"""
Intelligent document chunking for semantic search.
Uses semantic boundaries instead of fixed-size chunks.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of text with metadata."""
    text: str
    start: int
    end: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ChunkingStrategy:
    """Base class for chunking strategies."""
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        """Split text into chunks."""
        raise NotImplementedError


class FixedSizeChunker(ChunkingStrategy):
    """Fixed-size chunking with overlap."""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        """Split text into fixed-size chunks with overlap."""
        chunks = []
        text_length = len(text)
        
        start = 0
        chunk_index = 0
        
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            
            # Try to end at sentence boundary
            if end < text_length:
                for boundary in ['. ', '! ', '? ', '\n\n', '\n']:
                    boundary_pos = text.rfind(boundary, start, end)
                    if boundary_pos != -1 and boundary_pos > start + self.chunk_size // 2:
                        end = boundary_pos + len(boundary)
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    start=start,
                    end=end,
                    metadata={"chunk_index": chunk_index, "strategy": "fixed_size"}
                ))
                chunk_index += 1
            
            start = end - self.overlap
        
        return chunks


class SemanticChunker(ChunkingStrategy):
    """Chunk based on semantic boundaries (paragraphs, sections)."""
    
    def __init__(self, max_chunk_size: int = 512):
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        """Split text based on semantic boundaries."""
        # First, split by major sections
        sections = self._split_by_sections(text)
        
        chunks = []
        chunk_index = 0
        
        for section in sections:
            # Further split sections by paragraphs
            paragraphs = self._split_by_paragraphs(section['text'])
            
            for para in paragraphs:
                if len(para['text']) <= self.max_chunk_size:
                    # Paragraph fits in one chunk
                    chunks.append(Chunk(
                        text=para['text'],
                        start=section['start'] + para['start'],
                        end=section['start'] + para['end'],
                        metadata={
                            "chunk_index": chunk_index,
                            "strategy": "semantic",
                            "section": section.get('type', 'unknown'),
                            "is_paragraph": True
                        }
                    ))
                    chunk_index += 1
                else:
                    # Paragraph too large, use fixed-size within paragraph
                    fixed_chunker = FixedSizeChunker(
                        chunk_size=self.max_chunk_size,
                        overlap=20
                    )
                    sub_chunks = fixed_chunker.chunk(para['text'])
                    
                    for sub_chunk in sub_chunks:
                        chunks.append(Chunk(
                            text=sub_chunk.text,
                            start=section['start'] + para['start'] + sub_chunk.start,
                            end=section['start'] + para['start'] + sub_chunk.end,
                            metadata={
                                "chunk_index": chunk_index,
                                "strategy": "hybrid",
                                "section": section.get('type', 'unknown'),
                                "is_paragraph": False,
                                "parent_paragraph": True
                            }
                        ))
                        chunk_index += 1
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[Dict[str, Any]]:
        """Split text into sections based on headings and markers."""
        sections = []
        
        # Common section markers
        section_patterns = [
            (r'\n#{1,3}\s+(.+?)\n', 'heading'),  # Markdown headings
            (r'\n([A-Z][A-Z\s]{5,}):?\n', 'heading'),  # ALL CAPS headings
            (r'\n\d+\.\s+(.+?)\n', 'numbered'),  # Numbered sections
            (r'\n•\s+(.+?)\n', 'bullet'),  # Bullet points
        ]
        
        current_pos = 0
        current_section = {"text": "", "start": 0, "type": "body"}
        
        while current_pos < len(text):
            # Look for next section marker
            next_marker = None
            next_pos = len(text)
            
            for pattern, section_type in section_patterns:
                match = re.search(pattern, text[current_pos:], re.MULTILINE)
                if match and match.start() < next_pos - current_pos:
                    next_marker = (match, section_type)
                    next_pos = current_pos + match.start()
            
            # Extract current section
            section_text = text[current_pos:next_pos].strip()
            if section_text:
                current_section["text"] = section_text
                current_section["end"] = next_pos
                sections.append(current_section.copy())
            
            # Prepare for next section
            if next_marker:
                match, section_type = next_marker
                current_pos = current_pos + match.end()
                current_section = {
                    "text": "",
                    "start": current_pos,
                    "type": section_type,
                    "heading": match.group(1).strip() if match.groups() else ""
                }
            else:
                break
        
        # Add final section if any text remains
        if current_pos < len(text):
            section_text = text[current_pos:].strip()
            if section_text:
                current_section["text"] = section_text
                current_section["end"] = len(text)
                sections.append(current_section)
        
        return sections
    
    def _split_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Split text into paragraphs."""
        paragraphs = []
        
        # Split by double newlines (standard paragraph separation)
        para_texts = re.split(r'\n\s*\n', text)
        
        current_pos = 0
        for para_text in para_texts:
            if para_text.strip():
                paragraphs.append({
                    "text": para_text.strip(),
                    "start": current_pos,
                    "end": current_pos + len(para_text)
                })
            current_pos += len(para_text) + 2  # +2 for the "\n\n"
        
        return paragraphs


class RecursiveChunker(ChunkingStrategy):
    """Recursively chunk text using multiple strategies."""
    
    def __init__(self, max_chunk_size: int = 512):
        self.max_chunk_size = max_chunk_size
        self.semantic_chunker = SemanticChunker(max_chunk_size)
        self.fixed_chunker = FixedSizeChunker(
            chunk_size=max_chunk_size,
            overlap=50
        )
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        """Recursively chunk text, preferring semantic boundaries."""
        # First try semantic chunking
        semantic_chunks = self.semantic_chunker.chunk(text)
        
        # Check if any chunks are too large
        large_chunks = [c for c in semantic_chunks if len(c.text) > self.max_chunk_size * 1.5]
        
        if not large_chunks:
            return semantic_chunks
        
        # For large chunks, apply fixed-size chunking within them
        all_chunks = []
        chunk_index = 0
        
        for chunk in semantic_chunks:
            if len(chunk.text) > self.max_chunk_size * 1.5:
                # This chunk is too large, subdivide it
                sub_chunks = self.fixed_chunker.chunk(chunk.text)
                
                for sub_chunk in sub_chunks:
                    all_chunks.append(Chunk(
                        text=sub_chunk.text,
                        start=chunk.start + sub_chunk.start,
                        end=chunk.start + sub_chunk.end,
                        metadata={
                            "chunk_index": chunk_index,
                            "strategy": "recursive",
                            "parent_strategy": "semantic",
                            "was_large_chunk": True
                        }
                    ))
                    chunk_index += 1
            else:
                # Keep the semantic chunk
                chunk.metadata.update({
                    "chunk_index": chunk_index,
                    "strategy": "recursive",
                    "parent_strategy": "semantic",
                    "was_large_chunk": False
                })
                all_chunks.append(chunk)
                chunk_index += 1
        
        return all_chunks


class ChunkingFactory:
    """Factory to create chunking strategies."""
    
    @staticmethod
    def create_strategy(strategy: str = "recursive", **kwargs) -> ChunkingStrategy:
        """
        Create a chunking strategy.
        
        Args:
            strategy: One of "fixed", "semantic", "recursive"
            **kwargs: Strategy-specific parameters
            
        Returns:
            ChunkingStrategy instance
        """
        if strategy == "fixed":
            return FixedSizeChunker(**kwargs)
        elif strategy == "semantic":
            return SemanticChunker(**kwargs)
        elif strategy == "recursive":
            return RecursiveChunker(**kwargs)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    @staticmethod
    def get_strategy_info(strategy: str) -> dict:
        """Get information about chunking strategies."""
        strategies = {
            "fixed": {
                "description": "Fixed-size chunks with overlap",
                "best_for": "Uniform text, code, logs",
                "pros": "Simple, predictable, fast",
                "cons": "May break semantic units",
                "parameters": {"chunk_size": 512, "overlap": 50}
            },
            "semantic": {
                "description": "Chunk based on semantic boundaries",
                "best_for": "Documents with clear structure",
                "pros": "Preserves semantic units",
                "cons": "Slower, may create uneven chunks",
                "parameters": {"max_chunk_size": 512}
            },
            "recursive": {
                "description": "Recursive semantic then fixed chunking",
                "best_for": "Mixed content, general purpose",
                "pros": "Balanced, handles large sections",
                "cons": "More complex",
                "parameters": {"max_chunk_size": 512}
            }
        }
        
        return strategies.get(strategy, {})


# Test the chunking
if __name__ == "__main__":
    test_text = """
# SULV Construction Project

## Project Overview
SULV Construction is building a duplex in St Ives for client Yvette. 
The project includes two 4-bedroom units with sustainable features.

## Timeline
The project is scheduled for 6 months completion. 
Phase 1: Site preparation (2 weeks)
Phase 2: Foundation (3 weeks)
Phase 3: Framing (4 weeks)

## Budget
Total budget: $850,000
Materials: $500,000
Labor: $300,000
Contingency: $50,000

This is a detailed project plan that needs to be followed carefully.
All team members should review this document.
"""
    
    print("Testing chunking strategies...")
    
    # Test fixed chunking
    print("\n1. Fixed-size chunking:")
    fixed = ChunkingFactory.create_strategy("fixed", chunk_size=200, overlap=20)
    fixed_chunks = fixed.chunk(test_text)
    for i, chunk in enumerate(fixed_chunks[:3]):
        print(f"  Chunk {i}: {chunk.text[:80]}...")
    
    # Test semantic chunking
    print("\n2. Semantic chunking:")
    semantic = ChunkingFactory.create_strategy("semantic", max_chunk_size=300)
    semantic_chunks = semantic.chunk(test_text)
    for i, chunk in enumerate(semantic_chunks):
        print(f"  Chunk {i} ({chunk.metadata.get('section', 'unknown')}): {chunk.text[:80]}...")
    
    # Test recursive chunking
    print("\n3. Recursive chunking:")
    recursive = ChunkingFactory.create_strategy("recursive", max_chunk_size=250)
    recursive_chunks = recursive.chunk(test_text)
    for i, chunk in enumerate(recursive_chunks):
        strategy = chunk.metadata.get('strategy', 'unknown')
        print(f"  Chunk {i} ({strategy}): {chunk.text[:80]}...")