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
  - **Fallback**: If not set or not writable, automatically falls back to `/tmp/chroma_store`
  - **Docker**: If using `/data/chroma_store`, Dockerfile creates & owns the directory

## Deployment

This Space is automatically deployed via GitHub Actions when backend files are updated. The Dockerfile builds the FastAPI application with all dependencies and initializes the ChromaDB vector store.

## Architecture

- **FastAPI**: Web framework with async support
- **SQLAlchemy**: ORM with MySQL SSL support via PyMySQL
- **ChromaDB**: Vector database for RAG system
- **OpenAI**: AI embeddings and language models
- **Docker**: Containerized deployment