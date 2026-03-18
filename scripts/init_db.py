#!/usr/bin/env python3
"""
Initialize the unified knowledge base database.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.indexer import DocumentIndexer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database and create necessary directories."""
    
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    for subdir in ["inbox", "archive", "vectordb", "reports"]:
        (data_dir / subdir).mkdir(exist_ok=True)
    
    logger.info(f"Created data directory structure at {data_dir}")
    
    # Initialize database
    db_path = data_dir / "kb.db"
    indexer = DocumentIndexer(str(db_path))
    
    logger.info(f"Database initialized at {db_path}")
    
    # Create a test document to verify
    from models.document import IngestRequest, DocumentMetadata, DocumentSource, DocumentType
    
    test_request = IngestRequest(
        title="Welcome to SULV Unified Knowledge Base",
        content="This is the centralized knowledge core for all SULV administration tools.",
        metadata=DocumentMetadata(
            source=DocumentSource.LOCAL_FILE,
            document_type=DocumentType.TEXT,
            project_id="SULV-SYSTEM",
            sender="system",
            subject="System initialization",
            tags=["system", "welcome", "kb"]
        )
    )
    
    try:
        document = indexer.ingest_document(test_request)
        logger.info(f"Test document ingested: {document.id}")
        logger.info("✅ Database initialization complete!")
    except Exception as e:
        logger.error(f"Error ingesting test document: {e}")
        logger.info("⚠️  Database created but test ingestion failed")
    
    print("\nNext steps:")
    print("1. Start the API server: python src/core/api/server.py")
    print("2. Test the API: curl http://localhost:8000/api/v1/health")
    print("3. Check the database: sqlite3 data/kb.db '.tables'")


if __name__ == "__main__":
    main()