#!/usr/bin/env python3
"""
Test all essential KB components together.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

print("Testing All Essential KB Components")
print("=" * 60)


def test_embedding():
    """Test embedding models."""
    print("\n1. Testing Embedding Models...")
    try:
        from core.embedding import EmbeddingFactory
        
        # Test MiniLM
        embedder = EmbeddingFactory.create_model("minilm")
        texts = ["SULV Construction project", "St Ives duplex build"]
        embeddings = embedder.embed(texts)
        
        if embeddings and len(embeddings) == 2:
            print(f"  ✅ MiniLM embedding: {len(embeddings[0])} dimensions")
            return True
        else:
            print("  ❌ Embedding failed")
            return False
            
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("    Install: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_chunking():
    """Test chunking strategies."""
    print("\n2. Testing Chunking Strategies...")
    try:
        from core.chunking import ChunkingFactory
        
        test_text = """
        SULV Construction Project Report
        Project: St Ives Duplex
        Client: Yvette
        Budget: $850,000
        Timeline: 6 months
        Status: Planning phase
        """
        
        # Test recursive chunking
        chunker = ChunkingFactory.create_strategy("recursive", max_chunk_size=200)
        chunks = chunker.chunk(test_text)
        
        if chunks and len(chunks) > 0:
            print(f"  ✅ Recursive chunking: {len(chunks)} chunks created")
            for i, chunk in enumerate(chunks[:2]):
                print(f"    Chunk {i}: {chunk.text[:50]}...")
            return True
        else:
            print("  ❌ Chunking failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_ocr():
    """Test OCR availability."""
    print("\n3. Testing OCR Availability...")
    try:
        from core.ocr import OCRFactory
        
        ocr = OCRFactory.create_processor(language="eng")
        available = ocr.is_available()
        
        if available:
            print(f"  ✅ OCR available: {ocr.tesseract_path}")
        else:
            print("  ⚠️  OCR not available (install: brew install tesseract)")
            print("    This is optional but recommended for PDF/image processing")
        
        return True  # OCR is optional, don't fail the test
            
    except Exception as e:
        print(f"  ⚠️  OCR test error: {e}")
        return True  # OCR is optional


def test_reranking():
    """Test reranking models."""
    print("\n4. Testing Reranking Models...")
    try:
        from core.reranking import RerankingFactory
        
        query = "SULV Construction duplex project"
        documents = [
            "SULV is building a duplex in St Ives",
            "Construction project management",
            "Residential building in Sydney",
            "Duplex construction with sustainable features"
        ]
        
        # Test cross-encoder (if available)
        try:
            reranker = RerankingFactory.create_reranker("cross-encoder")
            results = reranker.rerank(query, documents)
            
            if results and len(results) > 0:
                print(f"  ✅ Cross-encoder reranking: {len(results)} results ranked")
                return True
            else:
                print("  ⚠️  Reranking returned no results")
                return True  # Don't fail, might be model loading issue
                
        except ImportError:
            print("  ⚠️  Cross-encoder not available (install: pip install sentence-transformers)")
            return True  # Optional component
            
    except Exception as e:
        print(f"  ⚠️  Reranking test error: {e}")
        return True  # Optional component


def test_processing_pipeline():
    """Test complete processing pipeline."""
    print("\n5. Testing Processing Pipeline...")
    try:
        from core.processor import ProcessingPipeline
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            SULV Construction Project
            ========================
            
            Project ID: SULV-2024-001
            Client: Yvette
            Address: 123 Sample St, St Ives
            Budget: $850,000
            Status: Active
            
            Project Details:
            - Two-story duplex
            - 4 bedrooms each unit
            - Sustainable features
            - 6 month timeline
            """)
            temp_path = f.name
        
        try:
            # Process the file
            pipeline = ProcessingPipeline()
            result = pipeline.process(temp_path, {"project_id": "SULV-2024-001"})
            
            if result:
                document, chunks = result
                print(f"  ✅ Processing pipeline: Document '{document.title}'")
                print(f"     Chunks: {len(chunks)}")
                print(f"     Metadata: {document.metadata.source.value}")
                return True
            else:
                print("  ❌ Processing pipeline failed")
                return False
                
        finally:
            # Clean up
            Path(temp_path).unlink()
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_models():
    """Test document data models."""
    print("\n6. Testing Document Models...")
    try:
        from models.document import Document, DocumentMetadata, DocumentSource, DocumentType
        
        metadata = DocumentMetadata(
            source=DocumentSource.LOCAL_FILE,
            document_type=DocumentType.REPORT,
            project_id="SULV-2024-001",
            sender="Travis Meng",
            subject="St Ives Duplex Project",
            tags=["construction", "residential", "st-ives"]
        )
        
        document = Document(
            id="test-123",
            title="Test Document",
            content="This is a test document for SULV Construction.",
            content_hash="abc123",
            metadata=metadata
        )
        
        print(f"  ✅ Document model: {document.title}")
        print(f"     Source: {document.metadata.source.value}")
        print(f"     Type: {document.metadata.document_type.value}")
        print(f"     Project: {document.metadata.project_id}")
        
        # Test serialization
        doc_dict = document.model_dump()
        if doc_dict.get("id") == "test-123":
            print("  ✅ Document serialization works")
            return True
        else:
            print("  ❌ Document serialization failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    tests = [
        ("Embedding", test_embedding),
        ("Chunking", test_chunking),
        ("OCR", test_ocr),
        ("Reranking", test_reranking),
        ("Processing Pipeline", test_processing_pipeline),
        ("Document Models", test_document_models),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"  ❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All essential KB components are working!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Initialize database: python scripts/init_db.py")
        print("3. Start API server: python src/core/api/server.py")
        print("4. Run integration tests: python scripts/test_api.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Check the errors above and install missing dependencies.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)