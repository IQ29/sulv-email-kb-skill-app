"""
Core indexing pipeline for the unified knowledge base.
Handles document ingestion, chunking, and dual indexing (FTS5 + semantic).
"""

import hashlib
import logging
from typing import List, Optional
from datetime import datetime

from ...models.document import (
    Document, DocumentChunk, DocumentStatus, 
    IngestRequest, DocumentMetadata
)

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Main indexer for the unified knowledge base."""
    
    def __init__(self, db_path: str = "./data/kb.db"):
        self.db_path = db_path
        self._setup_database()
        
    def _setup_database(self):
        """Initialize SQLite database with FTS5."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                source TEXT NOT NULL,
                document_type TEXT NOT NULL,
                project_id TEXT,
                sender TEXT,
                subject TEXT,
                status TEXT NOT NULL,
                indexed_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                metadata_json TEXT NOT NULL
            )
        """)
        
        # Create FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts 
            USING fts5(
                id UNINDEXED,
                title,
                content,
                source UNINDEXED,
                document_type UNINDEXED,
                project_id UNINDEXED,
                tokenize='porter'
            )
        """)
        
        # Create chunks table for semantic search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL,
                embedding BLOB,
                metadata_json TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def chunk_document(self, document: Document, chunk_size: int = 512, overlap: int = 50) -> List[DocumentChunk]:
        """Split document into overlapping chunks for semantic search."""
        chunks = []
        content = document.content
        content_length = len(content)
        
        start = 0
        chunk_index = 0
        
        while start < content_length:
            end = min(start + chunk_size, content_length)
            
            # Try to end at sentence boundary
            if end < content_length:
                # Look for sentence endings
                for boundary in ['. ', '! ', '? ', '\n\n', '\n']:
                    boundary_pos = content.rfind(boundary, start, end)
                    if boundary_pos != -1 and boundary_pos > start + chunk_size // 2:
                        end = boundary_pos + len(boundary)
                        break
            
            chunk_content = content[start:end].strip()
            if chunk_content:  # Skip empty chunks
                chunk_id = f"{document.id}_chunk_{chunk_index}"
                chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will be updated later
                    start_char=start,
                    end_char=end,
                    metadata={
                        "source": document.metadata.source.value,
                        "document_type": document.metadata.document_type.value,
                        "project_id": document.metadata.project_id,
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap  # Overlap for context
        
        # Update total chunks count
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def ingest_document(self, request: IngestRequest) -> Document:
        """Ingest a document into the unified knowledge base."""
        from uuid import uuid4
        
        # Create document ID
        doc_id = str(uuid4())
        content_hash = self.calculate_content_hash(request.content)
        
        # Check for duplicates
        if self._is_duplicate(content_hash):
            logger.info(f"Document with hash {content_hash} already exists, skipping")
            # TODO: Return existing document or update if force_reindex is True
        
        # Create document object
        document = Document(
            id=doc_id,
            title=request.title,
            content=request.content,
            content_hash=content_hash,
            metadata=request.metadata,
            status=DocumentStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store in SQLite
        self._store_document_sqlite(document)
        
        # Create chunks for semantic search
        chunks = self.chunk_document(document)
        
        # Store chunks
        self._store_chunks_sqlite(chunks)
        
        # Index in FTS5
        self._index_document_fts5(document)
        
        # TODO: Generate embeddings and store in Chroma
        # self._index_chunks_semantic(chunks)
        
        # Update document status
        document.status = DocumentStatus.INDEXED
        document.indexed_at = datetime.utcnow()
        self._update_document_status(document.id, DocumentStatus.INDEXED)
        
        logger.info(f"Ingested document {doc_id}: {request.title}")
        return document
    
    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if a document with the same content hash already exists."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM documents WHERE content_hash = ?",
            (content_hash,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def _store_document_sqlite(self, document: Document):
        """Store document in SQLite database."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents 
            (id, title, content, content_hash, source, document_type, project_id, 
             sender, subject, status, indexed_at, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document.id,
            document.title,
            document.content,
            document.content_hash,
            document.metadata.source.value,
            document.metadata.document_type.value,
            document.metadata.project_id,
            document.metadata.sender,
            document.metadata.subject,
            document.status.value,
            document.indexed_at.isoformat() if document.indexed_at else None,
            document.created_at.isoformat(),
            document.updated_at.isoformat(),
            json.dumps(document.metadata.dict())
        ))
        
        conn.commit()
        conn.close()
    
    def _store_chunks_sqlite(self, chunks: List[DocumentChunk]):
        """Store document chunks in SQLite database."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for chunk in chunks:
            cursor.execute("""
                INSERT INTO document_chunks 
                (id, document_id, content, chunk_index, total_chunks, 
                 start_char, end_char, embedding, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.id,
                chunk.document_id,
                chunk.content,
                chunk.chunk_index,
                chunk.total_chunks,
                chunk.start_char,
                chunk.end_char,
                None,  # embedding will be added later
                json.dumps(chunk.metadata),
                chunk.created_at.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _index_document_fts5(self, document: Document):
        """Index document in FTS5 virtual table."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents_fts 
            (id, title, content, source, document_type, project_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            document.id,
            document.title,
            document.content,
            document.metadata.source.value,
            document.metadata.document_type.value,
            document.metadata.project_id
        ))
        
        conn.commit()
        conn.close()
    
    def _update_document_status(self, document_id: str, status: DocumentStatus):
        """Update document status in database."""
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE documents 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (
            status.value,
            datetime.utcnow().isoformat(),
            document_id
        ))
        
        conn.commit()
        conn.close()