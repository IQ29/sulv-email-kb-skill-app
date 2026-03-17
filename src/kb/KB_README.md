# Enterprise Knowledge AI Platform

Option B: Slim Local MVP - Optimized for MBP 2016 (16GB RAM)

## Overview

A lightweight, modular AI knowledge base that ingests documents, indexes them for semantic search, and answers queries using local models with API fallback for complex reasoning.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ INGESTION PIPELINE                                          │
│ File → Parse → Clean → Chunk → Embed → Index               │
│ (Marker/Tesseract → Regex → Hybrid → MiniLM → Chroma)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ QUERY PIPELINE                                              │
│ Query → Intent → Rewrite → Embed → Search → Summarize → Gen │
│ (Rules → Rules → MiniLM → Chroma → Flan-T5 → Kimi API)     │
└─────────────────────────────────────────────────────────────┘
```

## Hardware Requirements

- **Target:** MacBook Pro 16" 2016, Intel i7, 16GB RAM
- **RAM Usage:** ~4-5GB when running
- **Storage:** ~2GB for models + document storage
- **GPU:** Not required (CPU-only)

## Quick Start

### Option 1: One-Command Start
```bash
./quickstart.sh
```

### Option 2: Step by Step
```bash
# 1. Run setup
./scripts/setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Download models (~2GB)
python scripts/download_models.py

# 4. Validate models
python scripts/validate_models.py

# 5. Run comprehensive tests
python scripts/test_models.py

# 6. Set API key (optional)
export KIMI_API_KEY='your-key'

# 7. Start using
python main.py stats
python main.py ingest ~/Documents/contract.pdf --user john

# 6. Query
python main.py query "What are the key terms?" --user john

# 7. Interactive chat
python main.py chat --user john
```

## Commands

### Ingest Documents
```bash
# Single file
python main.py ingest path/to/file.pdf --user john

# Directory
python main.py ingest path/to/folder/ --source gmail --user john
```

### Query
```bash
# Single query
python main.py query "Find contracts from last month" --user john

# Interactive chat
python main.py chat --user john
```

### Reports
```bash
# Daily report
python main.py report daily --date 2026-03-14 --user john

# Weekly report
python main.py report weekly --date 2026-03-14 --user john

# Monthly report
python main.py report monthly --date 2026-03 --user john
```

### Stats
```bash
python main.py stats
```

## Testing

### Quick Validation (after setup)
```bash
# Check if models are downloaded
python scripts/validate_models.py
```

### Comprehensive Testing
```bash
# Full test suite with example files
# Generates detailed report with performance metrics
python scripts/test_models.py

# View test report
cat data/reports/test_report_*.md
```

### Test Coverage
- ✅ Embedding model (MiniLM) - dimension, batch processing
- ✅ Vector database (Chroma) - add, search, persistence
- ✅ Text cleaner - normalization, entity extraction
- ✅ Text chunker - semantic boundaries, overlap
- ✅ Summarizer (Flan-T5) - compression, quality
- ✅ Document parsers - TXT, MD, JSON, PDF
- ✅ Full ingestion pipeline - end-to-end
- ✅ Query pipeline - intent, rewrite, search

## Model Stack

| Component | Model | Size | RAM |
|-----------|-------|------|-----|
| PDF Parser | Marker | 500MB | 1GB |
| OCR | Tesseract | 100MB | 500MB |
| Embeddings | all-MiniLM-L6-v2 | 80MB | 400MB |
| Summarizer | Flan-T5-small | 300MB | 800MB |
| Reasoning | Kimi API | - | - |
| **Total** | | **~1GB** | **~4-5GB** |

## Folder Structure

```
enterprise-kb/
├── config/
│   └── pipeline.yaml          # Configuration
├── src/
│   └── components/            # Modular components
│       ├── parsers/           # Document parsers
│       ├── cleaners/          # Text cleaners
│       ├── chunkers/          # Text chunkers
│       ├── embedders/         # Embedding models
│       ├── vectordbs/         # Vector databases
│       ├── summarizers/       # Summarizers
│       └── generators/        # LLM generators
├── data/
│   ├── inbox/                 # Staging area
│   ├── archive/               # Processed files
│   │   └── YYYY-MM-DD/
│   │       └── {user}/
│   ├── vectordb/              # Vector database
│   └── reports/               # Generated reports
│       ├── personal/{user}/
│       └── team/
│           ├── daily/
│           ├── weekly/
│           └── monthly/
├── main.py                    # CLI entry point
└── scripts/
    └── setup.sh               # Setup script
```

## Configuration

Edit `config/pipeline.yaml` to customize:

```yaml
pipeline:
  ingestion:
    parser: marker              # marker | tesseract
    embedder: minilm            # minilm | bge
    chunk_size: 512
    
  query:
    top_k: 10
    summarizer: flan_t5_small
    generator: api_fallback
    
api_fallback:
  provider: kimi
  model: kimi-k2.5
```

## Cost

- **Local processing:** $0
- **API fallback:** ~$5-10/month (depends on usage)
- **Total:** ~$5-10/month vs $200-500 for API-only

## Upgrade Path

### Phase 1: Foundation (Current)
- ✅ Document parsing (PDF, images)
- ✅ OCR for scanned docs
- ✅ Semantic search
- ✅ Daily/weekly/monthly reports
- ✅ API fallback for reasoning

### Phase 2: Intelligence
- Reranker (BGE-reranker)
- Query rewriter (Qwen-1.5B)
- Better classification
- Source citations

### Phase 3: Enterprise
- Document classifier (ModernBERT)
- NER entity extraction (GLiNER)
- Safety guard (PII detection)
- Audit logging

### Phase 4: Scale
- Local LLM (when you get M1/M2/M3 Mac)
- Multilingual support (NLLB)
- Workflow automation
- External connectors

## Troubleshooting

### Out of Memory
- Reduce `batch_size` in config
- Use smaller embedder (MiniLM vs BGE)
- Process fewer files at once

### Slow Processing
- First run downloads models (~2GB)
- Subsequent runs are faster
- Consider SSD for vector DB

### API Errors
- Check `KIMI_API_KEY` is set
- Check internet connection
- Falls back to local summarizer if API fails

## License

MIT

## Credits

Built with:
- [Sentence Transformers](https://www.sbert.net/)
- [ChromaDB](https://www.trychroma.com/)
- [Transformers](https://huggingface.co/docs/transformers/)
- [Marker](https://github.com/VikParuchuri/marker)
