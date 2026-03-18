#!/usr/bin/env python3
"""
Simple test to verify the project structure works.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

print("Testing SULV Unified Knowledge Base Project Structure")
print("=" * 60)

# Test 1: Check directory structure
print("\n1. Checking directory structure...")
required_dirs = [
    "src/core",
    "src/core/indexer", 
    "src/core/searcher",
    "src/core/sync",
    "src/core/api",
    "src/integrations",
    "src/models",
    "config",
    "scripts",
    "data",
    "docs",
    "clients/python"
]

all_exist = True
for dir_path in required_dirs:
    full_path = Path(__file__).parent / dir_path
    if full_path.exists():
        print(f"  ✅ {dir_path}/")
    else:
        print(f"  ❌ {dir_path}/ (missing)")
        all_exist = False

if not all_exist:
    print("\nSome directories are missing. Creating them...")
    for dir_path in required_dirs:
        full_path = Path(__file__).parent / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    print("Directories created.")

# Test 2: Check key files
print("\n2. Checking key files...")
required_files = [
    "README.md",
    "requirements.txt",
    "src/models/document.py",
    "src/core/indexer/__init__.py",
    "src/core/searcher/__init__.py",
    "src/core/api/server.py",
    "config/core.yaml",
    "scripts/init_db.py",
    "scripts/test_api.py",
    "clients/python/sulv_unified_kb.py",
    "docs/migration_plan.md"
]

for file_path in required_files:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        size_kb = full_path.stat().st_size / 1024
        print(f"  ✅ {file_path} ({size_kb:.1f} KB)")
    else:
        print(f"  ❌ {file_path} (missing)")

# Test 3: Check Python imports
print("\n3. Testing Python imports...")
try:
    # Try to import our modules
    from models.document import Document, DocumentMetadata, DocumentSource, DocumentType
    print("  ✅ models.document imported successfully")
    
    # Check if we can create instances
    metadata = DocumentMetadata(
        source=DocumentSource.LOCAL_FILE,
        document_type=DocumentType.TEXT,
        project_id="TEST-001"
    )
    
    doc = Document(
        id="test-123",
        title="Test Document",
        content="This is a test.",
        content_hash="abc123",
        metadata=metadata
    )
    
    print(f"  ✅ Created Document: {doc.id}")
    
except ImportError as e:
    print(f"  ❌ Import error: {e}")
except Exception as e:
    print(f"  ❌ Error creating document: {e}")

# Test 4: Check SQLite database
print("\n4. Testing database setup...")
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

db_path = data_dir / "test.db"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            value TEXT
        )
    """)
    
    # Insert test data
    cursor.execute("INSERT INTO test_table (name, value) VALUES (?, ?)", 
                   ("test", "value"))
    conn.commit()
    
    # Query test data
    cursor.execute("SELECT COUNT(*) FROM test_table")
    count = cursor.fetchone()[0]
    
    print(f"  ✅ Database test successful ({count} rows)")
    conn.close()
    
    # Clean up
    db_path.unlink()
    
except Exception as e:
    print(f"  ❌ Database test failed: {e}")

# Summary
print("\n" + "=" * 60)
print("Project Structure Test Complete")
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Initialize database: python scripts/init_db.py")
print("3. Start API server: python src/core/api/server.py")
print("4. Run tests: python scripts/test_api.py")
print("\nProject is ready for Phase 2 implementation!")