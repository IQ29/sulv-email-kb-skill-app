from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DocumentSource(str, Enum):
    """Sources from which documents can originate."""
    GMAIL = "gmail"
    GOOGLE_CHAT = "google_chat"
    GOOGLE_DRIVE = "google_drive"
    LOCAL_FILE = "local_file"
    EMAIL_SKILL = "email_skill"
    DASHBOARD = "dashboard"


class DocumentType(str, Enum):
    """Types of documents."""
    EMAIL = "email"
    CHAT_MESSAGE = "chat_message"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    IMAGE = "image"
    TEXT = "text"
    CONTRACT = "contract"
    PLAN = "plan"
    REPORT = "report"
    INVOICE = "invoice"


class DocumentStatus(str, Enum):
    """Processing status of documents."""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"
    ARCHIVED = "archived"


class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    source: DocumentSource
    document_type: DocumentType
    project_id: Optional[str] = Field(None, description="SULV project ID if applicable")
    sender: Optional[str] = Field(None, description="Email sender or author")
    recipients: List[str] = Field(default_factory=list)
    subject: Optional[str] = None
    conversation_id: Optional[str] = Field(None, description="For emails/chat threads")
    file_path: Optional[str] = Field(None, description="Local file path if applicable")
    google_id: Optional[str] = Field(None, description="Google resource ID")
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    language: str = "en"
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """A chunk of a document for indexing."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Core document model for the unified knowledge base."""
    id: str
    title: str
    content: str
    content_hash: str  # For deduplication
    metadata: DocumentMetadata
    status: DocumentStatus = DocumentStatus.PENDING
    indexed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResult(BaseModel):
    """Result from a search query."""
    document: Document
    score: float
    chunk: Optional[DocumentChunk] = None
    highlight: Optional[str] = None
    explanation: Optional[str] = None


class IngestRequest(BaseModel):
    """Request to ingest a document."""
    title: str
    content: str
    metadata: DocumentMetadata
    force_reindex: bool = False


class SearchRequest(BaseModel):
    """Request to search the knowledge base."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    offset: int = 0
    include_highlights: bool = True
    search_mode: str = "hybrid"  # "fts5", "semantic", or "hybrid"


class AskRequest(BaseModel):
    """Request for Q&A with AI context."""
    question: str
    context: Optional[Dict[str, Any]] = None
    max_context_documents: int = 5
    include_sources: bool = True


class AskResponse(BaseModel):
    """Response from Q&A."""
    answer: str
    sources: List[SearchResult] = Field(default_factory=list)
    confidence: float
    processing_time_ms: int