# 🌟 Aurora - AI-Powered Learning Platform

> **A learning platform that combines AI-powered skill navigation with basic progress tracking for corporate training.**

## 🎯 **Overview**

Aurora is a learning platform designed to help employees develop skills relevant to their company's actual projects. The system uses AI to generate personalized learning plans based on company documentation and provides basic progress tracking functionality.

## 🏗️ **System Architecture**

### **Frontend (Next.js 15)**
- React-based UI with TypeScript
- Real-time streaming responses
- Responsive design
- Chat-style interfaces

### **Backend (FastAPI + Python)**
- Async API with Python
- Modular agent architecture
- RESTful endpoints with streaming support
- Audit logging system

### **AI & Data Stack**
- **OpenAI GPT-4** for learning plan generation
- **ChromaDB** for vector storage and document search
- **LangChain** for RAG pipeline
- **Sentence Transformers** for document embeddings
- **MySQL** for structured data storage
- **CSV files** for resource and progress data

## 🤖 **System Components**

### **1. Welcome Agent** 👋
A basic onboarding component that:
- Provides platform introduction
- Explains available features
- Guides initial navigation

### **2. Skill Navigator** 🧭
The main AI-powered component that:
- **Analyzes user learning requests** using natural language processing
- **Retrieves relevant company project documentation** using RAG (Retrieval Augmented Generation)
- **Generates personalized 4-week learning plans** using OpenAI GPT-4
- **Recommends specific resources** from the company's learning catalog
- **Connects learning objectives** to actual company project requirements

**Technical Implementation:**
- Uses semantic search to find relevant project documentation
- Processes user queries to extract learning intent and technologies
- Generates structured learning plans with weekly goals and resources
- Streams responses in real-time for better user experience

### **3. Progress Companion** 📊
A simple CSV-based progress reader that:
- **Reads course data** from CSV files
- **Counts completed vs total courses** for basic metrics
- **Checks dates** to identify overdue items
- **Returns text summaries** of progress status

**Basic Functions:**
- Simple counting and percentage calculations
- Date comparison for overdue course identification
- Plain text status responses

## 🚀 **Key Features**

### **RAG-Powered Learning Plans**
- Company-specific knowledge retrieval from project documentation
- Contextual learning recommendations based on actual work needs
- Dynamic content that reflects current company projects
- Semantic search across all company documentation

### **Conversational Interface**
- Natural language queries in plain English
- Real-time streaming responses
- Context-aware conversations
- Multi-turn dialogue support

### **Basic Progress Tracking**
- File-based course data processing
- Simple completion calculations
- Overdue item identification
- Text-based progress summaries

## 📋 **Getting Started**

### **Prerequisites**
- Node.js 18+ and npm
- Python 3.9+ with pip
- MySQL database
- OpenAI API key

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
# Edit .env with your OpenAI API key and database credentials

# Initialize vector store with company documents
python -c "from rag import build_vectorstore; build_vectorstore('../data')"

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
│   ├── agents/                # Learning agents
│   │   ├── onboarding/        # Welcome agent
│   │   ├── skillnav/          # Skill Navigator (AI-powered)
│   │   └── progress/          # Progress Companion (CSV reader)
│   ├── app.py                 # Main FastAPI application
│   ├── rag.py                 # RAG system implementation
│   ├── settings.py            # Configuration
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js frontend
│   ├── src/app/               # Next.js app router
│   │   ├── agents/            # Agent interfaces
│   │   └── api/               # API proxy routes
│   └── components/            # UI components
├── data/                      # Training data and documents
│   ├── projects/              # Company project documentation
│   ├── policies/              # Company policies
│   └── resources/             # Learning resources catalog
└── README.md                  # This documentation
```

## 🛠️ **Technical Details**

### **Dependencies**
- **Core Framework**: FastAPI, Next.js 15, React, TypeScript
- **AI/ML**: OpenAI API, LangChain, ChromaDB, Sentence Transformers
- **Database**: MySQL, SQLAlchemy
- **Utilities**: Python-dotenv, Tenacity, Watchfiles

### **API Endpoints**
- `POST /agents/onboarding/stream` - Welcome agent interactions
- `POST /agents/skillnav/stream` - AI-powered learning plan generation
- `POST /agents/progress/stream` - Progress tracking queries
- Health check and audit endpoints available

### **Data Processing**
- Company documents processed into vector embeddings
- CSV files used for course and progress data
- Real-time streaming for AI responses
- Basic audit logging for all interactions

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Backend (.env)
OPENAI_API_KEY=your_openai_api_key
AURORA_DB_URL=mysql+mysqlconnector://user:pass@localhost:3306/aurora_db
AURORA_HMAC_KEY=your_secret_key

# Frontend (.env.local)
FASTAPI_URL=http://localhost:8000
```

### **Data Setup**
1. Place company project documentation in `data/projects/`
2. Update learning resources in `data/resources/catalog.csv`
3. Configure user progress data in `data/courses.csv`
4. Run vector store build to process documents

## 📈 **Usage Examples**

### **Skill Navigator Queries**
- "I want to learn backend development for our e-commerce platform"
- "Help me become an ML engineer for the AI analytics project"
- "What do I need to know for DevOps on our cloud infrastructure?"

### **Progress Tracking Queries**
- "What's my current progress?"
- "Which courses are overdue?"
- "How many courses have I completed?"

## 🔍 **Limitations**

- Progress tracking is basic CSV processing, not intelligent analysis
- Learning recommendations depend on quality of company documentation
- Requires OpenAI API access for AI features
- Vector database needs periodic rebuilding for document updates

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Aurora - AI-powered learning platform for corporate skill development*