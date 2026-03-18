# Migration Plan: From Three KB Systems to Unified KB

## Current State
Three overlapping knowledge base systems:
1. **sulv-knowledge-base** (🔒 Private) - Dedicated KB with SQLite FTS5, Claude Haiku
2. **sulv-dashboard** (🔒 Private) - Dashboard with KB Q&A interface, Claude integration  
3. **sulv-email-kb-skill-app** (🌐 Public) - Email skill with Chroma + MiniLM, Kimi API

## Target State
**sulv-unified-kb** - Single centralized knowledge core serving all three use cases

## Phase 1: Foundation (Week 1-2) ✅ COMPLETE

### ✅ Created Project Structure
```
sulv-unified-kb/
├── src/core/           # Core KB engine
├── src/integrations/   # Integration adapters
├── src/models/         # Data models
├── config/            # Configuration
├── scripts/           # Utility scripts
├── tests/             # Test suite
├── docs/              # Documentation
└── clients/           # Client libraries
```

### ✅ Implemented Core Components
1. **Document models** - Unified data model for all document types
2. **DocumentIndexer** - Dual indexing (SQLite FTS5 + planned Chroma semantic)
3. **UnifiedSearcher** - Hybrid search combining FTS5 and semantic
4. **FastAPI Server** - REST API with health, ingest, search, Q&A endpoints
5. **Python Client** - Client library for easy integration

### ✅ Basic Features Working
- ✅ Document ingestion with deduplication
- ✅ FTS5 full-text search with ranking
- ✅ Hybrid search architecture (semantic placeholder)
- ✅ Q&A interface with context retrieval
- ✅ Dashboard and email skill integration endpoints
- ✅ Health monitoring and metrics

## Phase 2: Integration & Data Migration (Week 3-4)

### 2.1 Data Migration from Existing Systems
```
sulv-knowledge-base (SQLite FTS5) → sulv-unified-kb
    • Export existing documents and metadata
    • Convert to unified document model
    • Preserve search indexes

sulv-dashboard (Claude Q&A) → sulv-unified-kb API
    • Update dashboard to use unified KB API
    • Migrate Q&A context logic
    • Preserve UI/UX

sulv-email-kb-skill-app (Chroma + MiniLM) → sulv-unified-kb
    • Export semantic embeddings
    • Migrate email processing logic
    • Update skill to use unified API
```

### 2.2 Google Workspace Sync
- Implement Gmail, Chat, Drive sync adapters
- Real-time webhook support for new emails/chat messages
- Incremental sync with change detection

### 2.3 Semantic Search Integration
- Integrate Chroma vector database
- Add MiniLM embeddings for semantic search
- Implement hybrid ranking algorithm

## Phase 3: AI Enhancement (Week 5-6)

### 3.1 Claude/Kimi Integration
- Add Claude Haiku for report generation (from sulv-knowledge-base)
- Add Claude for Q&A (from sulv-dashboard)
- Add Kimi API fallback (from sulv-email-kb-skill-app)
- Implement intelligent routing between AI providers

### 3.2 Advanced Q&A
- Context-aware question answering
- Multi-document synthesis
- Source citation and confidence scoring
- Conversation memory

### 3.3 Report Generation
- Daily/weekly/monthly report templates
- Automated report scheduling
- Email distribution of reports
- Google Chat integration for notifications

## Phase 4: Production Deployment (Week 7-8)

### 4.1 Performance Optimization
- Database indexing optimization
- Query caching layer
- Async processing for large documents
- Rate limiting and load balancing

### 4.2 Monitoring & Alerting
- Comprehensive logging
- Performance metrics collection
- Health check automation
- Alerting for sync failures

### 4.3 Security Hardening
- API authentication (JWT/OAuth)
- Rate limiting per client
- Input validation and sanitization
- Audit logging

### 4.4 Documentation & Training
- API documentation
- Integration guides for each system
- Troubleshooting guide
- Training for SULV staff

## Integration Points for Existing Systems

### For sulv-dashboard:
```typescript
// Before: Direct database access
const results = await localDatabase.search("query");

// After: Unified KB API
import { SULVKnowledgeBase } from '@sulv/unified-kb-client';
const kb = new SULVKnowledgeBase({ baseUrl: 'http://kb-api.sulv.com.au' });
const results = await kb.search({ query: "query", search_mode: "hybrid" });
```

### For sulv-email-kb-skill-app:
```python
# Before: Direct Chroma access
from chromadb import Chroma
db = Chroma(persist_directory="./chroma_db")
results = db.query(query_texts=["email query"])

# After: Unified KB API
from sulv_unified_kb import SULVUnifiedKBClient
client = SULVUnifiedKBClient(base_url="http://kb-api.sulv.com.au")
context = client.get_email_context(sender, subject, body)
```

### For sulv-knowledge-base:
```python
# Before: Direct SQLite FTS5
import sqlite3
conn = sqlite3.connect("knowledge_base.db")
cursor = conn.execute("SELECT * FROM documents_fts WHERE documents_fts MATCH ?", [query])

# After: Unified KB API (or direct migration)
# Option 1: Migrate data to unified KB
# Option 2: Use unified KB as primary, keep legacy as read-only backup
```

## Rollback Plan

### If issues occur during migration:
1. **Immediate rollback**: Switch back to using original systems
2. **Data preservation**: All original data remains intact
3. **Gradual migration**: Migrate one system at a time
4. **A/B testing**: Run both systems in parallel during transition

### Rollback triggers:
- API response time > 2 seconds
- Search accuracy drops below 90%
- Data loss or corruption detected
- User complaints about missing functionality

## Success Metrics

### Technical Metrics:
- ✅ API response time < 500ms for search queries
- ✅ 99.9% API availability
- ✅ Search recall > 95% compared to original systems
- ✅ Data migration completeness 100%

### Business Metrics:
- ✅ Reduced maintenance overhead by 60%
- ✅ Improved search relevance (user satisfaction)
- ✅ Faster new feature development
- ✅ Reduced API costs through unified AI routing

## Timeline

```
Week 1-2: Foundation (COMPLETE)
    • Project structure
    • Core indexing/search
    • Basic API

Week 3-4: Integration
    • Data migration tools
    • Google Workspace sync
    • Semantic search integration

Week 5-6: AI Enhancement  
    • Claude/Kimi integration
    • Advanced Q&A
    • Report generation

Week 7-8: Production
    • Performance optimization
    • Monitoring & security
    • Documentation & training

Week 9: Go-live & Monitoring
    • Gradual cutover
    • Performance monitoring
    • User feedback collection
```

## Risks & Mitigation

### Risk: Data loss during migration
**Mitigation**: 
- Comprehensive backup before migration
- Dry-run migration on test data
- Parallel operation during transition
- Data validation scripts

### Risk: Performance degradation
**Mitigation**:
- Load testing before production
- Query optimization
- Caching layer implementation
- Gradual user migration

### Risk: Integration complexity
**Mitigation**:
- Clear API contracts
- Comprehensive documentation
- Integration test suite
- Developer support during transition

## Next Immediate Steps

1. **Test current implementation**: Run `python scripts/test_api.py`
2. **Set up development environment**: Run `python setup.py`
3. **Review API design**: Check `src/core/api/server.py`
4. **Plan data migration**: Analyze existing data structures
5. **Schedule integration meetings**: With dashboard and email skill teams

## Contact & Support

- **Project Lead**: OpenClaw AI Assistant
- **Technical Lead**: [To be assigned]
- **SULV Stakeholder**: Ian
- **GitHub**: https://github.com/IQ29/sulv-unified-kb (to be created)
- **Documentation**: `./docs/` directory