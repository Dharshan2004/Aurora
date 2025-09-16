# 🌟 Aurora - AI Ecosystem for Professional Development

> **An AI ecosystem that empowers young professionals from onboarding to leadership by providing personalized guidance, skills growth planning, and transparent feedback.**

## 🎯 **Vision & Mission**

Aurora is an AI ecosystem designed to empower young professionals throughout their career journey - from initial onboarding to leadership roles. Our mission aligns with SAP's motto: **"help the world run better and improve people's lives"** while showcasing Responsible AI and business scalability.

The platform provides personalized guidance, skills growth planning, and transparent feedback to help young professionals navigate their career development within the SAP ecosystem and beyond.

## 🏗️ **System Architecture**

### **Frontend (Next.js 15)**
- **React 18** with TypeScript for type safety
- **Real-time streaming responses** with progressive loading
- **Responsive design** with Tailwind CSS
- **Multi-agent chat interfaces** with agent-specific UI
- **Dynamic height containers** to prevent content truncation
- **Loading indicators** with agent-specific messaging

### **Backend (FastAPI + Python)**
- **Async API** with Python 3.9+
- **Modular agent architecture** with specialized AI agents
- **RESTful endpoints** with streaming support
- **Comprehensive audit logging** system
- **Health monitoring** with detailed system status

### **AI & Data Stack**
- **OpenAI GPT-4** for intelligent learning plan generation
- **Qdrant** for high-performance vector storage and semantic search
- **LangChain** for RAG pipeline and agent orchestration
- **HuggingFace Embeddings** (sentence-transformers/all-MiniLM-L6-v2)
- **MySQL** for structured data storage
- **CSV files** for resource and progress data

## 🤖 **AI Agents**

### **1. Welcome Agent** 👋
**Purpose**: Onboarding FAQs and policy guidance for young professionals
- **RAG-powered responses** using company documentation and handbooks
- **Policy document filtering** for accurate onboarding information
- **Source attribution** with document references for transparency
- **Streaming responses** for real-time interaction

**Key Capabilities**:
- Answers onboarding FAQs from policy documents and handbooks
- Provides guidance on company policies, benefits, and procedures
- Offers transparent, source-backed responses for new employees
- Supports young professionals in their initial company integration

### **2. Skill Navigator Agent** 🧭
**Purpose**: Personalized 30-60 day learning plans for professional development
- **Skills gap analysis** with targeted learning recommendations
- **SAP Learning Hub integration** for relevant course content
- **Career-focused planning** aligned with professional growth goals
- **Adaptive learning paths** that evolve with individual progress

**Key Features**:
- Analyzes user learning requests using natural language processing
- Retrieves relevant company project documentation using RAG
- Generates personalized 4-week learning plans with specific goals
- Recommends resources from company learning catalog
- Connects learning objectives to actual company project requirements

### **3. Progress Companion** 📊
**Purpose**: Learning progress tracking and motivational feedback
- **Progress analysis** with intelligent insights and recommendations
- **Achievement tracking** with milestone recognition
- **Motivational feedback** to maintain engagement
- **Next steps guidance** for continued professional development

## 🚀 **Key Features**

### **Personalized Professional Development**
- **Career-focused guidance** from onboarding to leadership
- **Skills gap analysis** with targeted learning recommendations
- **SAP Learning Hub integration** for relevant course content
- **Transparent feedback** on progress and achievements
- **Responsible AI** practices with explainable decisions

### **Intelligent Learning Planning**
- **30-60 day structured plans** tailored to individual needs
- **Skills-based recommendations** aligned with career goals
- **Learning path optimization** based on current competencies
- **Progress tracking** with motivational feedback
- **Adaptive planning** that evolves with professional growth

### **Advanced AI Technology**
- **Qdrant vector database** for high-performance semantic search
- **RAG-powered responses** using company documentation
- **Real-time streaming** for interactive user experience
- **Multi-agent architecture** for specialized assistance
- **Comprehensive monitoring** with audit trails

### **Comprehensive Monitoring**
- **Health check endpoints** with detailed system status
- **Vector store monitoring** with document counts
- **Agent performance tracking** with latency metrics
- **Debug logging** for troubleshooting
- **Audit trail** for all interactions

## 📋 **Getting Started**

### **Prerequisites**
- **Node.js 18+** and npm
- **Python 3.9+** with pip
- **MySQL database** (local or cloud)
- **OpenAI API key**
- **Qdrant instance** (local or cloud)

### **Installation**

#### **1. Clone Repository**
```bash
git clone https://github.com/your-org/aurora.git
cd aurora
```

#### **2. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration:
# OPENAI_API_KEY=your_openai_api_key
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=your_qdrant_api_key
# QDRANT_COLLECTION=aurora_docs
# AUTO_INGEST=1
# SEED_DATA_DIR=./data

# Start backend server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### **3. Frontend Setup**
```bash
cd frontend
npm install

# Configure environment variables
echo "FASTAPI_URL=http://localhost:8000" > .env.local

# Start frontend server
npm run dev
```

#### **4. Access Application**
Open browser to `http://localhost:3000`

## 📊 **Project Structure**

```
Aurora/
├── backend/                    # FastAPI backend
│   ├── agents/                # AI learning agents
│   │   ├── onboarding/        # Welcome agent (RAG-powered)
│   │   ├── skillnav/          # Skill Navigator (AI-powered)
│   │   └── progress/          # Progress Companion (CSV reader)
│   ├── app.py                 # Main FastAPI application
│   ├── rag.py                 # RAG system implementation
│   ├── vectorstore.py         # Qdrant vector store management
│   ├── orchestrator.py        # Agent orchestration
│   ├── settings.py            # Configuration management
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js frontend
│   ├── src/app/               # Next.js app router
│   │   ├── agents/            # Agent interfaces
│   │   │   ├── welcome/       # Welcome agent page
│   │   │   ├── skillnav/      # Skill Navigator page
│   │   │   └── progress/      # Progress Companion page
│   │   └── api/               # API proxy routes
│   │       └── aurora/        # Backend proxy
│   ├── components/            # UI components
│   │   └── ChatStream.tsx     # Streaming chat component
│   └── lib/                   # Utility libraries
├── data/                      # Training data and documents
│   ├── projects/              # Company project documentation
│   ├── policies/              # Company policies
│   ├── resources/             # Learning resources catalog
│   └── seed/                  # Seed data for auto-ingestion
└── README.md                  # This documentation
```

## 🛠️ **Technical Details**

### **Dependencies**
- **Core Framework**: FastAPI, Next.js 15, React 18, TypeScript
- **AI/ML**: OpenAI API, LangChain, Qdrant, HuggingFace Embeddings
- **Database**: MySQL, SQLAlchemy, Qdrant Client
- **Utilities**: Python-dotenv, Tenacity, Watchfiles, Uvicorn

### **API Endpoints**
- `GET /healthz` - Comprehensive health check with system status
- `POST /agents/onboarding/stream` - Welcome agent with RAG responses
- `POST /agents/skillnav/stream` - AI-powered learning plan generation
- `POST /agents/progress/stream` - Progress tracking and analysis
- `GET /admin/audit/*` - Audit trail and monitoring endpoints

### **Environment Variables**

#### **Backend Configuration**
```bash
# Required
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=aurora_docs

# Optional
AUTO_INGEST=1                    # Auto-ingest documents on startup
SEED_DATA_DIR=./data             # Directory for seed documents
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
AURORA_DB_URL=mysql+mysqlconnector://user:pass@localhost:3306/aurora_db
AURORA_HMAC_KEY=your_secret_key
```

#### **Frontend Configuration**
```bash
# Required
FASTAPI_URL=http://localhost:8000
```

## 📈 **Usage Examples**

### **Welcome Agent Queries**
- "What is the company leave policy?"
- "How do I request vacation time?"
- "What are the company benefits?"
- "Tell me about the onboarding process"
- "What should I know as a new employee?"

### **Skill Navigator Queries**
- "Create a 30-day learning plan for a junior developer role"
- "I need to improve my Python and cloud skills for career growth"
- "Plan my development from junior to senior developer"
- "What should I learn for data science career advancement?"
- "Help me become a technical lead in 60 days"

### **Progress Companion Queries**
- "What's my current learning progress?"
- "Which courses are overdue?"
- "What should I focus on next for career growth?"

## 🔧 **Configuration & Deployment**

### **Qdrant Setup**
1. **Local Qdrant**: `docker run -p 6333:6333 qdrant/qdrant`
2. **Cloud Qdrant**: Use Qdrant Cloud with API key
3. **Collection**: Automatically created with dimension inference

### **Data Setup**
1. Place company project documentation in `data/projects/`
2. Update learning resources in `data/resources/catalog.csv`
3. Configure user progress data in `data/courses.csv`
4. Set `AUTO_INGEST=1` for automatic document processing

### **Production Deployment**
- Use environment variables for all configuration
- Enable SSL for database connections
- Set up proper logging and monitoring
- Configure backup strategies for vector store

## 🔍 **Recent Improvements**

### **Professional Development Focus**
- ✅ **Career-Centric Design**: Aligned with SAP's mission and values
- ✅ **Young Professional Focus**: Tailored for onboarding to leadership journey
- ✅ **Responsible AI**: Transparent, explainable decision-making
- ✅ **Business Scalability**: Architecture designed for enterprise growth

### **Technical Enhancements**
- ✅ **Qdrant Integration**: High-performance vector database for semantic search
- ✅ **Auto-ingestion**: Automatic document processing for seamless onboarding
- ✅ **Robust Error Handling**: Fallback mechanisms for reliable operation
- ✅ **Debug Logging**: Comprehensive logging for troubleshooting and transparency
- ✅ **Health Monitoring**: Detailed system status for operational excellence

### **User Experience Improvements**
- ✅ **Dynamic Height**: Responsive containers preventing content truncation
- ✅ **Agent-Specific UI**: Tailored interfaces for each professional development stage
- ✅ **Loading Indicators**: Contextual loading messages with progress feedback
- ✅ **Better Typography**: Improved readability for professional content
- ✅ **Error Handling**: User-friendly error messages and recovery mechanisms

### **AI Agent Enhancements**
- ✅ **Welcome Agent**: Enhanced onboarding FAQ responses with policy integration
- ✅ **Skill Navigator**: Improved 30-60 day learning plan generation
- ✅ **Progress Companion**: Enhanced progress tracking with motivational feedback
- ✅ **Streaming**: Real-time response streaming for interactive professional development

## 🚨 **Troubleshooting**

### **Common Issues**
1. **Vector Store Empty**: Check `AUTO_INGEST=1` and document files
2. **Agent Responses**: Verify OpenAI API key and Qdrant connection
3. **Frontend Truncation**: Ensure dynamic height containers are working
4. **Streaming Issues**: Check network connectivity and proxy configuration

### **Debug Commands**
```bash
# Check vector store status
curl http://localhost:8000/healthz

# Test agent responses
curl -X POST http://localhost:8000/agents/onboarding/stream \
  -H "Content-Type: application/json" \
  -d '{"msg": "What is the leave policy?"}'

# Check document count
python -c "from rag import get_document_count; print(get_document_count())"
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Aurora - AI ecosystem empowering young professionals from onboarding to leadership with personalized guidance, skills growth planning, and transparent feedback*