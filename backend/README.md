# Aurora Backend

FastAPI-based backend for the Aurora learning management system with AI-powered agents.

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

4. Run the application:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Deploying to HuggingFace Spaces

**IMPORTANT:** Before deployment, ensure you complete these steps:

### Pre-deployment Checklist

1. **📋 Paste Aiven CA Certificate**
   - Obtain the CA certificate from your Aiven MySQL service
   - Paste the full certificate content into `backend/ca.pem`
   - Replace the placeholder content with the actual certificate

2. **⚙️ Configure Space Variables/Secrets**
   Set these environment variables in your HF Space settings:
   - `AURORA_DB_URL`: Your MySQL connection string (format: `mysql+pymysql://USER:PASS@HOST:PORT/DBNAME?charset=utf8mb4`)
   - `MYSQL_SSL_CA_PATH`: Set to `/app/ca.pem`
   - `OPENAI_API_KEY`: Your OpenAI API key (if using AI features)
   - `AURORA_HMAC_KEY`: Secure key for integrity checks

3. **🐳 Space Configuration**
   - Ensure Space type is set to **"Docker"**
   - Confirm the application runs on port **7860** (HF Spaces requirement)
   - The Dockerfile handles the rest of the configuration

4. **🔒 SSL Connection**
   - The app is configured to use SSL when connecting to Aiven MySQL
   - The CA certificate at `/app/ca.pem` will be used for SSL verification
   - Pool settings are optimized for free tier usage

### Architecture

- **FastAPI** web framework with async support
- **SQLAlchemy** ORM with MySQL SSL support via PyMySQL
- **AI Agents** for onboarding, skill navigation, and progress tracking
- **RAG System** using ChromaDB and OpenAI embeddings
- **CORS** enabled for frontend integration

### API Endpoints

- `GET /health` - Health check
- `POST /v1/agents/execute` - Execute specific agent
- `POST /v1/aurora` - Smart routing to appropriate agent
- `POST /agents/{agent_name}/stream` - Streaming responses for real-time UX
- `GET /admin/audit/*` - Audit trail endpoints

### Database

The application uses MySQL with SSL support for production deployment. The database configuration includes:
- Conservative pool settings for free tier compatibility
- SSL certificate verification for secure connections
- Connection pre-ping and recycling for reliability
