"""
Python client library for the SULV Unified Knowledge Base API.
"""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ...src.models.document import (
    Document, SearchResult, IngestRequest, SearchRequest, AskRequest, AskResponse,
    DocumentMetadata, DocumentSource, DocumentType
)


class SULVUnifiedKBClient:
    """Client for interacting with the SULV Unified Knowledge Base API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API server
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def health(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    def ingest(self, request: IngestRequest) -> Document:
        """Ingest a document into the knowledge base."""
        response = self.session.post(
            f"{self.base_url}/api/v1/ingest",
            json=request.dict()
        )
        response.raise_for_status()
        return Document(**response.json())
    
    def ingest_simple(
        self,
        title: str,
        content: str,
        source: DocumentSource,
        document_type: DocumentType,
        project_id: Optional[str] = None,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Document:
        """Simplified document ingestion."""
        metadata = DocumentMetadata(
            source=source,
            document_type=document_type,
            project_id=project_id,
            sender=sender,
            subject=subject,
            tags=tags or []
        )
        
        request = IngestRequest(
            title=title,
            content=content,
            metadata=metadata
        )
        
        return self.ingest(request)
    
    def search(self, request: SearchRequest) -> List[SearchResult]:
        """Search the knowledge base."""
        response = self.session.post(
            f"{self.base_url}/api/v1/search",
            json=request.dict()
        )
        response.raise_for_status()
        
        results = []
        for item in response.json():
            # Convert nested document dict to Document object
            doc_dict = item.pop("document")
            document = Document(**doc_dict)
            
            # Convert chunk if present
            chunk = None
            if "chunk" in item and item["chunk"]:
                from ...src.models.document import DocumentChunk
                chunk = DocumentChunk(**item["chunk"])
            
            result = SearchResult(
                document=document,
                score=item["score"],
                chunk=chunk,
                highlight=item.get("highlight"),
                explanation=item.get("explanation")
            )
            results.append(result)
        
        return results
    
    def search_simple(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        search_mode: str = "hybrid"
    ) -> List[SearchResult]:
        """Simplified search."""
        request = SearchRequest(
            query=query,
            filters=filters,
            limit=limit,
            search_mode=search_mode
        )
        return self.search(request)
    
    def ask(self, request: AskRequest) -> AskResponse:
        """Ask a question with AI context."""
        response = self.session.post(
            f"{self.base_url}/api/v1/ask",
            json=request.dict()
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Convert sources to SearchResult objects
        sources = []
        for source_dict in data.get("sources", []):
            doc_dict = source_dict.pop("document")
            document = Document(**doc_dict)
            
            chunk = None
            if "chunk" in source_dict and source_dict["chunk"]:
                from ...src.models.document import DocumentChunk
                chunk = DocumentChunk(**source_dict["chunk"])
            
            source = SearchResult(
                document=document,
                score=source_dict["score"],
                chunk=chunk,
                highlight=source_dict.get("highlight"),
                explanation=source_dict.get("explanation")
            )
            sources.append(source)
        
        return AskResponse(
            answer=data["answer"],
            sources=sources,
            confidence=data["confidence"],
            processing_time_ms=data["processing_time_ms"]
        )
    
    def ask_simple(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        max_context_documents: int = 5,
        include_sources: bool = True
    ) -> AskResponse:
        """Simplified Q&A."""
        request = AskRequest(
            question=question,
            context=context,
            max_context_documents=max_context_documents,
            include_sources=include_sources
        )
        return self.ask(request)
    
    def get_document(self, document_id: str) -> Document:
        """Get a document by ID."""
        response = self.session.get(f"{self.base_url}/api/v1/documents/{document_id}")
        response.raise_for_status()
        return Document(**response.json())
    
    def get_project_documents(self, project_id: str, limit: int = 50) -> List[Document]:
        """Get all documents for a specific project."""
        response = self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}/documents",
            params={"limit": limit}
        )
        response.raise_for_status()
        
        documents = []
        for doc_dict in response.json():
            documents.append(Document(**doc_dict))
        
        return documents
    
    def get_recent_documents(self, limit: int = 20) -> List[Document]:
        """Get most recently indexed documents."""
        response = self.session.get(
            f"{self.base_url}/api/v1/documents/recent",
            params={"limit": limit}
        )
        response.raise_for_status()
        
        documents = []
        for doc_dict in response.json():
            documents.append(Document(**doc_dict))
        
        return documents
    
    # Dashboard integration methods
    def dashboard_search(self, request: SearchRequest) -> List[SearchResult]:
        """Dashboard-optimized search."""
        response = self.session.post(
            f"{self.base_url}/api/v1/integrations/dashboard/search",
            json=request.dict()
        )
        response.raise_for_status()
        
        results = []
        for item in response.json():
            doc_dict = item.pop("document")
            document = Document(**doc_dict)
            
            chunk = None
            if "chunk" in item and item["chunk"]:
                from ...src.models.document import DocumentChunk
                chunk = DocumentChunk(**item["chunk"])
            
            result = SearchResult(
                document=document,
                score=item["score"],
                chunk=chunk,
                highlight=item.get("highlight"),
                explanation=item.get("explanation")
            )
            results.append(result)
        
        return results
    
    def get_email_context(
        self,
        sender: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Get context for email processing."""
        response = self.session.post(
            f"{self.base_url}/api/v1/integrations/email/context",
            params={
                "sender": sender,
                "subject": subject,
                "body": body
            }
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = SULVUnifiedKBClient()
    
    # Check health
    health = client.health()
    print(f"API Health: {health}")
    
    # Ingest a document
    document = client.ingest_simple(
        title="Test Document",
        content="This is a test document for the unified knowledge base.",
        source=DocumentSource.LOCAL_FILE,
        document_type=DocumentType.TEXT,
        project_id="TEST-001",
        tags=["test", "example"]
    )
    print(f"Ingested document: {document.id}")
    
    # Search for documents
    results = client.search_simple("test document")
    print(f"Found {len(results)} results")
    
    # Ask a question
    answer = client.ask_simple("What is this test about?")
    print(f"Q&A Answer: {answer.answer[:100]}...")