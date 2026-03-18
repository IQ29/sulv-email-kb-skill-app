"""
FastAPI server for the unified knowledge base API.
"""

import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ...models.document import (
    Document, SearchResult, IngestRequest, SearchRequest, AskRequest, AskResponse
)
from ..indexer import DocumentIndexer
from ..searcher import UnifiedSearcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SULV Unified Knowledge Base API",
    description="Centralized knowledge core for all SULV administration tools",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (in production, use dependency injection)
indexer = None
searcher = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    indexed_documents: int


def get_indexer():
    """Dependency to get indexer instance."""
    global indexer
    if indexer is None:
        indexer = DocumentIndexer()
    return indexer


def get_searcher():
    """Dependency to get searcher instance."""
    global searcher
    if searcher is None:
        searcher = UnifiedSearcher()
    return searcher


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global indexer, searcher
    logger.info("Starting SULV Unified Knowledge Base API")
    indexer = DocumentIndexer()
    searcher = UnifiedSearcher()
    logger.info("Services initialized")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirects to docs."""
    return {"message": "SULV Unified Knowledge Base API - See /docs for API documentation"}


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check(
    indexer: DocumentIndexer = Depends(get_indexer),
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Health check endpoint."""
    import sqlite3
    import os
    
    # Check database
    db_path = "./data/kb.db"
    db_exists = os.path.exists(db_path)
    
    # Count documents
    indexed_count = 0
    if db_exists:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'indexed'")
            indexed_count = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="connected" if db_exists else "not_found",
        indexed_documents=indexed_count
    )


@app.post("/api/v1/ingest", response_model=Document)
async def ingest_document(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    indexer: DocumentIndexer = Depends(get_indexer)
):
    """Ingest a document into the knowledge base."""
    try:
        # Ingest document (could be moved to background task for large documents)
        document = indexer.ingest_document(request)
        return document
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@app.post("/api/v1/search", response_model=List[SearchResult])
async def search_documents(
    request: SearchRequest,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Search the knowledge base."""
    try:
        results = searcher.search(request)
        return results
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/v1/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Ask a question with AI context from the knowledge base."""
    try:
        # First, search for relevant documents
        search_request = SearchRequest(
            query=request.question,
            limit=request.max_context_documents,
            search_mode="hybrid"
        )
        
        search_results = searcher.search(search_request)
        
        if not search_results:
            return AskResponse(
                answer="I couldn't find any relevant information in the knowledge base to answer your question.",
                sources=[],
                confidence=0.0,
                processing_time_ms=0
            )
        
        # TODO: Integrate with Claude/Kimi API for actual Q&A
        # For now, return a simple response with search results
        
        # Build context from search results
        context_parts = []
        for result in search_results[:3]:  # Use top 3 results
            context_parts.append(f"Document: {result.document.title}")
            if result.highlight:
                context_parts.append(f"Relevant excerpt: {result.highlight}")
        
        context = "\n\n".join(context_parts)
        
        # Simple template-based answer (replace with AI in Phase 3)
        answer = f"Based on the knowledge base, I found {len(search_results)} relevant documents. "
        answer += "Here's what I found:\n\n"
        answer += context
        
        return AskResponse(
            answer=answer,
            sources=search_results if request.include_sources else [],
            confidence=0.7,  # Placeholder confidence
            processing_time_ms=100  # Placeholder
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


@app.get("/api/v1/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Get a document by ID."""
    document = searcher.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get("/api/v1/projects/{project_id}/documents", response_model=List[Document])
async def get_project_documents(
    project_id: str,
    limit: int = 50,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Get all documents for a specific project."""
    documents = searcher.get_documents_by_project(project_id, limit)
    return documents


@app.get("/api/v1/documents/recent", response_model=List[Document])
async def get_recent_documents(
    limit: int = 20,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Get most recently indexed documents."""
    documents = searcher.get_recent_documents(limit)
    return documents


# Integration endpoints for specific tools
@app.post("/api/v1/integrations/dashboard/search", response_model=List[SearchResult])
async def dashboard_search(
    request: SearchRequest,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Dashboard-optimized search endpoint."""
    # Add dashboard-specific filters or processing
    if not request.filters:
        request.filters = {}
    
    # Dashboard typically wants recent, relevant documents
    request.search_mode = "hybrid"
    request.limit = min(request.limit, 50)  # Limit for dashboard
    
    return await search_documents(request, searcher)


@app.post("/api/v1/integrations/email/context")
async def email_context_lookup(
    sender: str,
    subject: str,
    body: str,
    searcher: UnifiedSearcher = Depends(get_searcher)
):
    """Get context for email processing."""
    # Search for similar emails or related documents
    query = f"{subject} {body[:200]}"
    search_request = SearchRequest(
        query=query,
        filters={"source": "gmail"},
        limit=5,
        search_mode="hybrid"
    )
    
    results = searcher.search(search_request)
    
    return {
        "context_found": len(results) > 0,
        "relevant_documents": [
            {
                "id": r.document.id,
                "title": r.document.title,
                "relevance_score": r.score,
                "highlight": r.highlight
            }
            for r in results
        ],
        "suggested_tags": self._suggest_tags(results)
    }
    
    def _suggest_tags(self, results: List[SearchResult]) -> List[str]:
        """Suggest tags based on search results."""
        tags = set()
        for result in results:
            if result.document.metadata.tags:
                tags.update(result.document.metadata.tags[:3])
            if result.document.metadata.project_id:
                tags.add(f"project:{result.document.metadata.project_id}")
        
        return list(tags)[:5]


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )