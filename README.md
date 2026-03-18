# SULV Unified Knowledge Base

## 🎯 Vision
A centralized knowledge core that serves as the single source of truth for all SULV administration tools, replacing overlapping KB functionality across:
- `sulv-knowledge-base` (current dedicated KB)
- `sulv-dashboard` (KB Q&A interface)
- `sulv-email-kb-skill-app` (email processing with KB context)

## 🏗️ Architecture (Option 1 - Centralized Core)

```
┌─────────────────────────────────────────────────────────┐
│               UNIFIED KB CORE                           │
│  • SQLite FTS5 (primary full-text index)                │
│  • Chroma + MiniLM (semantic search layer)              │
│  • Claude/Kimi API integration (AI reasoning)           │
│  • Unified data sync (Gmail/Chat/Drive/Local)           │
│                                                         │
│  ESSENTIAL ELEMENTS (Tiny Models, No LLM Cost):         │
│  • Embedding: MiniLM-L6-v2 (80MB)                       │
│  • Chunking: Recursive semantic                         │
│  • OCR: Tesseract (100MB)                               │
│  • Reranking: Cross-encoder (80MB)                      │
│  • Processing: Complete pipeline                        │
└─────────────────────────────────────────────────────────┘
            │              │              │
            ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Dashboard  │  │ Email Skill │  │ Other Tools │
│  (Q&A UI)   │  │ (Context)   │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

## 📁 Project Structure

```
sulv-unified-kb/
├── src/
│   ├── core/                    # Core KB engine
│   │   ├── indexer/            # Indexing pipeline
│   │   ├── searcher/           # Search algorithms
│   │   ├── sync/               # Data sync from sources
│   │   ├── api/                # Unified API layer
│   │   ├── embedding/          # Embedding models (MiniLM, BGE, FastText)
│   │   ├── chunking/           # Intelligent chunking strategies
│   │   ├── ocr/                # OCR for images/PDFs (Tesseract)
│   │   ├── reranking/          # Result reranking (cross-encoders)
│   │   └── processor/          # Complete processing pipeline
│   ├── integrations/           # Integration adapters
│   │   ├── dashboard/          # Dashboard integration
│   │   ├── email_skill/        # Email skill integration
│   │   └── google_workspace/   # Google services
│   └── models/                 # Data models
├── config/                     # Configuration
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── docs/                       # Documentation
├── ESSENTIAL_ELEMENTS.md       # Complete KB components guide
└── clients/                    # Client libraries
    ├── python/                 # Python client
    ├── typescript/             # TypeScript client (for dashboard)
    └── cli/                    # Command-line interface
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- SQLite3
- Google Workspace credentials (for sync)

### Installation
```bash
# Clone and setup
cd sulv-unified-kb
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Configure Google Workspace
python scripts/setup_google_auth.py
```

### Quick Start
```bash
# Start the unified KB server
python src/api/server.py

# In another terminal, test the API
curl http://localhost:8000/api/v1/health
```

## 🔌 API Endpoints

### Core API
- `GET /api/v1/health` - Service health check
- `POST /api/v1/ingest` - Ingest documents/data
- `POST /api/v1/search` - Unified search (full-text + semantic)
- `POST /api/v1/ask` - Q&A with AI context
- `GET /api/v1/sync/status` - Sync status from sources

### Integration Endpoints
- `POST /api/v1/integrations/dashboard/search` - Dashboard-optimized search
- `POST /api/v1/integrations/email/context` - Email context lookup
- `POST /api/v1/integrations/google/sync` - Trigger Google sync

## 🔄 Data Flow

### Ingestion Pipeline
```
Source (Gmail/Chat/Drive/Local) 
    → [Sync Adapter] 
    → [Parser/Cleaner] 
    → [Chunker] 
    → [Dual Index: SQLite FTS5 + Chroma] 
    → [Metadata Store]
```

### Query Pipeline
```
Query 
    → [Intent Classifier] 
    → [Query Rewriter] 
    → [Dual Search: FTS5 + Semantic] 
    → [Result Fusion] 
    → [AI Context Enrichment] 
    → [Response Formatter]
```

## 🎨 Integration Examples

### Dashboard Integration (TypeScript)
```typescript
import { SULVKnowledgeBase } from '@sulv/unified-kb-client';

const kb = new SULVKnowledgeBase({ baseUrl: 'http://localhost:8000' });

// Search for project documents
const results = await kb.search({
  query: 'St Ives duplex construction plans',
  filters: { source: 'drive', project: 'SULV-2024-001' }
});

// Q&A interface
const answer = await kb.ask({
  question: 'What are the current issues with the St Ives project?',
  context: { project_id: 'SULV-2024-001' }
});
```

### Email Skill Integration (Python)
```python
from sulv_unified_kb import UnifiedKBClient

kb = UnifiedKBClient(api_url="http://localhost:8000")

# Get context for email processing
context = kb.get_email_context(
    sender="client@example.com",
    subject="St Ives project inquiry",
    body="Looking for updates on the duplex construction..."
)

# Ingest processed email
kb.ingest_email(
    email_id="email_123",
    sender="client@example.com",
    subject="Project inquiry",
    body="...",
    attachments=[...],
    metadata={"project": "SULV-2024-001"}
)
```

## 📊 Features

### Unified Search
- **Full-text search**: SQLite FTS5 for keyword matching
- **Semantic search**: Chroma + MiniLM for meaning-based search
- **Hybrid ranking**: Combines both approaches for best results
- **Faceted filtering**: By source, date, project, type

### AI Integration
- **Claude Haiku**: Report generation and complex Q&A
- **Kimi API**: Fallback reasoning and summarization
- **Local models**: MiniLM for embeddings, Flan-T5 for summarization

### Data Sync
- **Google Workspace**: Gmail, Chat, Drive
- **Local files**: Documents, PDFs, images
- **Real-time updates**: Webhook support
- **Incremental sync**: Only new/changed content

## 🔧 Configuration

### Core Config (`config/core.yaml`)
```yaml
database:
  path: ./data/kb.db
  fts5_enabled: true
  
search:
  hybrid_weight_fts5: 0.4
  hybrid_weight_semantic: 0.6
  top_k: 10
  
ai:
  primary: claude_haiku
  fallback: kimi
  local_embedding: minilm_l6_v2
  
sync:
  google:
    enabled: true
    interval_minutes: 15
  local:
    enabled: true
    watch_paths: ["./data/inbox"]
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test specific components
pytest tests/test_core_indexer.py
pytest tests/test_api_integration.py

# Integration tests
pytest tests/integration/test_dashboard_client.py
```

## 📈 Migration Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Core indexing pipeline
- [ ] Unified API server
- [ ] Basic search functionality
- [ ] SQLite FTS5 integration

### Phase 2: Integration (Week 3-4)
- [ ] Google Workspace sync
- [ ] Dashboard client library
- [ ] Email skill integration
- [ ] Semantic search layer

### Phase 3: AI Enhancement (Week 5-6)
- [ ] Claude/Kimi integration
- [ ] Q&A interface
- [ ] Report generation
- [ ] Result fusion algorithms

### Phase 4: Migration (Week 7-8)
- [ ] Data migration from existing systems
- [ ] Update dashboard to use unified API
- [ ] Update email skill to use unified API
- [ ] Decommission overlapping components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

MIT

## 🙏 Acknowledgments

- Built on lessons from `sulv-knowledge-base`, `sulv-dashboard`, and `sulv-email-kb-skill-app`
- Integrates best practices from all three systems
- Designed for SULV Construction operational excellence