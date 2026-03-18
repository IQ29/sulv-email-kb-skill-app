#!/usr/bin/env python3
"""
Test the unified knowledge base API.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.document import IngestRequest, DocumentMetadata, DocumentSource, DocumentType, SearchRequest


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get("http://localhost:8000/api/v1/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(response.text)
        return False


def test_ingest():
    """Test document ingestion."""
    print("\nTesting document ingestion...")
    
    request = IngestRequest(
        title="SULV St Ives Duplex Project Plan",
        content="""Project: St Ives Duplex Construction
Client: Yvette
Address: 123 Sample Street, St Ives NSW 2075
Project ID: SULV-2024-001
Status: Planning phase
Budget: $850,000
Timeline: 6 months
Key Contacts:
- Travis Meng (Project Manager)
- Ian (SULV Admin)
- Yvette (Client)

Project Details:
- Two-story duplex
- 4 bedrooms each unit
- Double garage
- Sustainable features: solar panels, rainwater tank
- Council approval pending

Next Steps:
1. Finalize architectural plans
2. Submit DA to Ku-ring-gai Council
3. Secure construction loan
4. Schedule site preparation""",
        metadata=DocumentMetadata(
            source=DocumentSource.LOCAL_FILE,
            document_type=DocumentType.REPORT,
            project_id="SULV-2024-001",
            sender="Travis Meng",
            subject="St Ives Duplex Project Plan",
            recipients=["ian@sulv.com.au", "yvette@example.com"],
            tags=["duplex", "st-ives", "planning", "construction"]
        )
    )
    
    response = requests.post(
        "http://localhost:8000/api/v1/ingest",
        json=request.dict()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Document ingested: {data['id']}")
        print(f"   Title: {data['title']}")
        print(f"   Project: {data['metadata']['project_id']}")
        return data['id']
    else:
        print(f"❌ Ingestion failed: {response.status_code}")
        print(response.text)
        return None


def test_search(document_id: str):
    """Test search functionality."""
    print("\nTesting search...")
    
    # Search for the ingested document
    request = SearchRequest(
        query="St Ives duplex construction",
        filters={"project_id": "SULV-2024-001"},
        limit=5
    )
    
    response = requests.post(
        "http://localhost:8000/api/v1/search",
        json=request.dict()
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Search returned {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['document']['title']} (score: {result['score']:.3f})")
            if result['highlight']:
                print(f"     Highlight: {result['highlight'][:100]}...")
        
        # Verify our document is in results
        found = any(r['document']['id'] == document_id for r in results)
        if found:
            print("✅ Ingested document found in search results")
        else:
            print("⚠️  Ingested document not found in search results")
        
        return results
    else:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        return None


def test_ask():
    """Test Q&A functionality."""
    print("\nTesting Q&A...")
    
    request = {
        "question": "What is the budget for the St Ives duplex project?",
        "max_context_documents": 3,
        "include_sources": True
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/ask",
        json=request
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Q&A response received")
        print(f"   Answer: {data['answer'][:200]}...")
        print(f"   Confidence: {data['confidence']:.2f}")
        print(f"   Sources: {len(data['sources'])} documents")
        return data
    else:
        print(f"❌ Q&A failed: {response.status_code}")
        print(response.text)
        return None


def test_dashboard_integration():
    """Test dashboard-specific endpoint."""
    print("\nTesting dashboard integration...")
    
    request = SearchRequest(
        query="project",
        limit=10,
        search_mode="hybrid"
    )
    
    response = requests.post(
        "http://localhost:8000/api/v1/integrations/dashboard/search",
        json=request.dict()
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Dashboard search returned {len(results)} results")
        return results
    else:
        print(f"❌ Dashboard search failed: {response.status_code}")
        print(response.text)
        return None


def main():
    """Run all tests."""
    print("=" * 60)
    print("SULV Unified Knowledge Base API Test Suite")
    print("=" * 60)
    
    # Wait for server to start
    print("Waiting for API server to be ready...")
    time.sleep(2)
    
    # Run tests
    tests_passed = 0
    tests_total = 5
    
    # Test 1: Health
    if test_health():
        tests_passed += 1
    
    # Test 2: Ingest
    document_id = test_ingest()
    if document_id:
        tests_passed += 1
    
    # Test 3: Search (requires successful ingestion)
    if document_id:
        if test_search(document_id):
            tests_passed += 1
    
    # Test 4: Q&A
    if test_ask():
        tests_passed += 1
    
    # Test 5: Dashboard integration
    if test_dashboard_integration():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Summary: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Unified KB API is working correctly.")
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed.")
        print("   Check that the API server is running: python src/core/api/server.py")
    
    return tests_passed == tests_total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)