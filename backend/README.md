---
title: Aurora Backend API
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "4.21.0"
app_file: app.py
pinned: false
---

# Aurora Backend API

AI-powered backend for the Aurora learning management system with personalized guidance, skills growth planning, and transparent feedback.

## Features

- **Welcome Agent**: Onboarding FAQ agent with streaming responses
- **Skill Navigator**: Personalized 30-60 day learning plans
- **Progress Companion**: Learning progress tracking and motivation
- **RAG System**: ChromaDB with OpenAI embeddings
- **MySQL SSL**: Secure database connections with Aiven
- **Audit Trail**: Transparent AI decision tracking

## API Endpoints

- `GET /health` - Health check
- `POST /v1/agents/execute` - Execute specific agent
- `POST /v1/aurora` - Smart routing to appropriate agent
- `POST /agents/{agent_name}/stream` - Streaming responses
- `GET /admin/audit/*` - Audit trail endpoints

## Environment Variables

Required environment variables (set in Space settings):

- `AURORA_DB_URL`: MySQL connection string (required)
- `MYSQL_SSL_CA_PATH`: SSL certificate path (default: `/app/ca.pem`)
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `AURORA_HMAC_KEY`: Secure key for integrity checks
- `AURORA_ENV`: Environment (`production`)
- `AURORA_INDEX_VERSION`: Index version (`v1`)

### ChromaDB Configuration

- `CHROMA_DIR`: ChromaDB persistence directory (optional)
  - **Recommended**: Set to `/tmp/chroma_store` in Space vars for zero-friction demo
  - **Fallback**: If not set or not writable, automatically falls back to `/tmp/chroma_store/<timestamp>`
  - **Docker**: If using `/data/chroma_store`, Dockerfile creates & owns the directory
- `CHROMA_RESET`: Reset ChromaDB store on startup (optional)
  - Set to `1` or `true` to clear the store for a clean demo
  - Use once if permissions or stale locks occur

### ChromaDB Storage

**Recommended environment variables:**
- `CHROMA_DIR=/tmp/chroma_store` - Use ephemeral storage for demos
- `CHROMA_RESET=1` - Clear store once if permissions or stale locks occur

**Notes:**
- `/tmp` is ephemeral across rebuilds (fine for demos)
- ChromaDB automatically falls back to writable directories if configured path fails
- Startup logs show the final chosen directory and writability status

### RAG Bootstrap

**Environment variables for auto-ingestion:**
- `CHROMA_DIR=/tmp/chroma_store` - ChromaDB persistence directory
- `CHROMA_AUTO_INGEST=1` - Auto-build vectors if store is empty at startup
- `SEED_DATA_DIR=./data/seed` - Directory containing demo files (markdown/txt/pdf)
- `ALLOW_ADMIN=1` - Enable `POST /admin/reindex` endpoint for manual reindexing

**Features:**
- Automatic ingestion of seed data when store is empty
- Document count logging on startup
- Admin reindex endpoint for rebuilding vectors on demand
- Retrieval telemetry for debugging empty results

### ChromaDB Recovery

**Environment variables for robust persistence:**
- `CHROMA_DIR=/tmp/chroma_store` - ChromaDB persistence directory (single source of truth)
- `CHROMA_FORCE_CLEAN=1` - Force clean directory if readonly errors occur
- `CHROMA_RESET=1` - Explicitly wipe and rebuild store (use deliberately)
- `CHROMA_AUTO_INGEST=1` - Auto-ingest seed data if store is empty

**Recovery features:**
- Automatic fallback to `/tmp/chroma_store/<timestamp>` if configured path fails
- Self-healing from readonly database errors
- Modern duckdb+parquet backend (avoids SQLite issues)
- Write-probe testing before initialization
- Force clean option for stubborn readonly issues

**Notes:**
- ChromaDB automatically recovers from readonly errors
- Use `CHROMA_FORCE_CLEAN=1` for one deploy if you hit readonly errors
- Use `CHROMA_RESET=1` deliberately to wipe and rebuild
- Startup logs show resolved path, backend type, and writability status

## Deployment

This Space is automatically deployed via GitHub Actions when backend files are updated. The Dockerfile builds the FastAPI application with all dependencies and initializes the ChromaDB vector store.

## Architecture

- **FastAPI**: Web framework with async support
- **SQLAlchemy**: ORM with MySQL SSL support via PyMySQL
- **ChromaDB**: Vector database for RAG system
- **OpenAI**: AI embeddings and language models
- **Docker**: Containerized deployment