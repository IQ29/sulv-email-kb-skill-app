---
name: sulv-google-workspace-hybrid
description: Hybrid Google Workspace integration combining google-workspace MCP for Chat with gog CLI for Gmail/Drive. Use when: (1) Accessing Google Chat spaces/threads, (2) Synchronizing emails and attachments from Gmail, (3) Managing Google Drive files, (4) Sending automated reports to Chat spaces, (5) Need resilient fallback between two Google Workspace access methods. Specifically designed for SULV Build operations requiring Chat integration with robust email/attachment handling.
---

# SULV Google Workspace Hybrid Skill

## Overview

This skill provides a unified interface to Google Workspace by combining the strengths of two existing skills:
- **google-workspace MCP** (via `mcporter`): Best for Google Chat operations
- **gog CLI** (via `gog`): Robust for Gmail and Drive operations

The hybrid approach ensures reliable access to all Google Workspace services with automatic fallback between backends.

## Core Architecture

### Backend Selection Logic
```
User Request → Skill Router → Best Backend
                                ├── Google Chat → google-workspace MCP (only option)
                                ├── Gmail → Try google-workspace, fallback to gog
                                └── Google Drive → Prefer gog, fallback to google-workspace
```

### Key Advantages
1. **Chat Coverage**: Only `google-workspace` supports Google Chat API
2. **Email Resilience**: Dual backend for Gmail operations
3. **Drive Reliability**: `gog` has mature Drive support
4. **Automatic Fallback**: If one backend fails, try the other
5. **SULV Optimized**: Tailored for reporting workflows

## Quick Start

### Prerequisites
Ensure both backends are available:
```bash
# Check google-workspace MCP
mcporter config list | grep google-workspace

# Check gog CLI
which gog
```

### Basic Operations

#### 1. Google Chat Operations (google-workspace only)
```bash
# List Chat spaces
mcporter call --server google-workspace --tool "chat.listSpaces"

# Send message to space
mcporter call --server google-workspace --tool "chat.sendMessage" spaceId="spaces/xxx" text="Report update"
```

#### 2. Gmail Operations (Hybrid)
```bash
# Try google-workspace first, fallback to gog
# See scripts/email_sync.py for implementation
python scripts/email_sync.py --query "label:SULV-Build"
```

#### 3. Drive Operations (gog preferred)
```bash
# Search Drive files
gog drive search "SULV Build" --max 10
```

## Workflow: SULV Daily Reporting

### Step 1: Sync Emails & Attachments
```bash
python scripts/email_sync.py \
  --query "from:admin_auto@sulv.com.au newer_than:1d" \
  --download-attachments \
  --output-dir ./data/emails
```

### Step 2: Process Data
```bash
python scripts/process_reports.py \
  --input-dir ./data/emails \
  --template references/report_template.md
```

### Step 3: Post to Google Chat
```bash
python scripts/chat_reporter.py \
  --space "spaces/SULV-Build-Leadership" \
  --report ./output/daily_report.md
```

## Backend Configuration

### google-workspace MCP Setup
```bash
# Install if not present
npm install -g @presto-ai/google-workspace-mcp
mcporter config add google-workspace --command "npx" --arg "-y" --arg "@presto-ai/google-workspace-mcp"

# First use opens browser for OAuth
mcporter call --server google-workspace --tool "people.getMe"
```

### gog CLI Setup
```bash
# Install via Homebrew
brew install steipete/tap/gogcli

# Authenticate (requires client_secret.json)
gog auth credentials /path/to/client_secret.json
gog auth add admin_auto@sulv.com.au --services gmail,calendar,drive
```

## Error Handling & Fallback

The skill implements smart fallback:
1. **Primary attempt**: Use preferred backend for each service
2. **Timeout detection**: 30-second timeout per operation
3. **Fallback logic**: If primary fails, try alternative backend
4. **Logging**: All attempts logged to `logs/hybrid_operations.log`

Example fallback sequence for Gmail search:
```python
# Try google-workspace first
try:
    results = mcporter.call('google-workspace', 'gmail.search', {query: q})
except (TimeoutError, ConnectionError):
    # Fallback to gog
    results = exec(f'gog gmail search "{q}" --max 100 --json')
```

## Resources

### scripts/
- `email_sync.py` - Hybrid email synchronization with attachment download
- `chat_reporter.py` - Post reports to Google Chat spaces
- `drive_manager.py` - Unified Drive file operations
- `hybrid_backend.py` - Core backend selection and fallback logic

### references/
- `google_chat_api.md` - Google Chat API reference and space IDs
- `sulv_reporting_workflow.md` - SULV-specific reporting procedures
- `error_handling_guide.md` - Troubleshooting backend failures

## Common Use Cases

### 1. Daily Email Digest
- Sync emails from `admin_auto@sulv.com.au`
- Download attachments (contracts, plans, photos)
- Generate summary report
- Post to `SULV-Build-Leadership` space

### 2. Project Space Monitoring
- Monitor all SULV project Chat spaces
- Detect rule violations (from SULV Operations Manual)
- Post corrective reminders
- Log to audit trail

### 3. Drive Structure Audit
- Verify project folder templates
- Check naming conventions
- Identify misplaced files
- Generate compliance report

## Troubleshooting

### Backend Authentication Issues
```bash
# Reset google-workspace auth
mcporter call --server google-workspace --tool "auth.clear"

# Check gog auth status
gog auth list
```

### Rate Limiting
- Both backends have separate rate limits
- Implement exponential backoff in scripts
- Monitor `logs/rate_limits.log`

### Service Availability
- Google Chat: Only via google-workspace
- Gmail: Both backends (prefer google-workspace)
- Drive: Both backends (prefer gog)

---
*Skill designed for SULV Build Google Workspace System Operations*
