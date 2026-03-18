"""
Unified search module combining FTS5 and semantic search.
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...models.document import (
    Document, DocumentChunk, SearchResult, SearchRequest,
    DocumentSource, DocumentType, DocumentMetadata
)

logger = logging.getLogger(__name__)


class UnifiedSearcher:
    """Combines FTS5 full-text search with semantic search."""
    
    def __init__(self, db_path: str = "./data/kb.db"):
        self.db_path = db_path
        
    def search(self, request: SearchRequest) -> List[SearchResult]:
        """Perform unified search based on search_mode."""
        if request.search_mode == "fts5":
            return self._search_fts5(request)
        elif request.search_mode == "semantic":
            return self._search_semantic(request)
        elif request.search_mode == "hybrid":
            return self._search_hybrid(request)
        else:
            raise ValueError(f"Unknown search mode: {request.search_mode}")
    
    def _search_fts5(self, request: SearchRequest) -> List[SearchResult]:
        """Perform FTS5 full-text search."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build WHERE clause for filters
        where_clauses = []
        params = [request.query]
        
        if request.filters:
            for key, value in request.filters.items():
                if key in ["source", "document_type", "project_id"]:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # FTS5 search with ranking
        query = f"""
            SELECT 
                d.id, d.title, d.content, d.content_hash, d.source, d.document_type,
                d.project_id, d.sender, d.subject, d.status, d.indexed_at,
                d.created_at, d.updated_at, d.metadata_json,
                bm25(documents_fts) as rank
            FROM documents_fts
            JOIN documents d ON documents_fts.id = d.id
            WHERE documents_fts MATCH ?
                AND {where_sql}
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        
        params.extend([request.limit, request.offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            document = self._row_to_document(row)
            score = 1.0 / (row["rank"] + 1)  # Convert bm25 to similarity score
            
            # Generate highlight if requested
            highlight = None
            if request.include_highlights:
                highlight = self._generate_highlight(document.content, request.query)
            
            result = SearchResult(
                document=document,
                score=score,
                highlight=highlight
            )
            results.append(result)
        
        return results
    
    def _search_semantic(self, request: SearchRequest) -> List[SearchResult]:
        """Perform semantic search (placeholder for Chroma integration)."""
        # TODO: Implement Chroma semantic search
        logger.warning("Semantic search not yet implemented, falling back to FTS5")
        return self._search_fts5(request)
    
    def _search_hybrid(self, request: SearchRequest) -> List[SearchResult]:
        """Combine FTS5 and semantic search results."""
        fts5_results = self._search_fts5(request)
        
        # TODO: Get semantic results and combine
        # semantic_results = self._search_semantic(request)
        
        # For now, just return FTS5 results
        return fts5_results
    
    def _row_to_document(self, row) -> Document:
        """Convert SQLite row to Document object."""
        import json
        
        metadata_dict = json.loads(row["metadata_json"])
        
        metadata = DocumentMetadata(
            source=DocumentSource(metadata_dict.get("source", "local_file")),
            document_type=DocumentType(metadata_dict.get("document_type", "text")),
            project_id=metadata_dict.get("project_id"),
            sender=metadata_dict.get("sender"),
            recipients=metadata_dict.get("recipients", []),
            subject=metadata_dict.get("subject"),
            conversation_id=metadata_dict.get("conversation_id"),
            file_path=metadata_dict.get("file_path"),
            google_id=metadata_dict.get("google_id"),
            size_bytes=metadata_dict.get("size_bytes"),
            mime_type=metadata_dict.get("mime_type"),
            language=metadata_dict.get("language", "en"),
            tags=metadata_dict.get("tags", []),
            custom_fields=metadata_dict.get("custom_fields", {})
        )
        
        # Parse timestamps
        def parse_timestamp(ts):
            if ts:
                try:
                    return datetime.fromisoformat(ts)
                except (ValueError, TypeError):
                    return None
            return None
        
        return Document(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            content_hash=row["content_hash"],
            metadata=metadata,
            status=row["status"],
            indexed_at=parse_timestamp(row["indexed_at"]),
            created_at=parse_timestamp(row["created_at"]),
            updated_at=parse_timestamp(row["updated_at"])
        )
    
    def _generate_highlight(self, content: str, query: str, context_chars: int = 100) -> Optional[str]:
        """Generate a text highlight around query terms."""
        import re
        
        # Simple highlight: find first occurrence of any query word
        query_words = re.findall(r'\w+', query.lower())
        content_lower = content.lower()
        
        for word in query_words:
            if len(word) < 3:  # Skip very short words
                continue
                
            pos = content_lower.find(word)
            if pos != -1:
                # Extract context around the match
                start = max(0, pos - context_chars)
                end = min(len(content), pos + len(word) + context_chars)
                
                # Try to start at sentence boundary
                for boundary in ['. ', '! ', '? ', '\n\n', '\n']:
                    boundary_pos = content.rfind(boundary, start, pos)
                    if boundary_pos != -1:
                        start = boundary_pos + len(boundary)
                        break
                
                highlight = content[start:end]
                if start > 0:
                    highlight = "..." + highlight
                if end < len(content):
                    highlight = highlight + "..."
                
                return highlight
        
        return None
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by its ID."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents WHERE id = ?
        """, (document_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_document(row)
        return None
    
    def get_documents_by_project(self, project_id: str, limit: int = 50) -> List[Document]:
        """Get all documents for a specific project."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents 
            WHERE project_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (project_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_document(row) for row in rows]
    
    def get_recent_documents(self, limit: int = 20) -> List[Document]:
        """Get most recently indexed documents."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents 
            WHERE status = 'indexed'
            ORDER BY indexed_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_document(row) for row in rows]