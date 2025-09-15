from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from vectorstore import init_vector_store, vector_count, add_texts, is_qdrant_available
import os
import time

# Read EMBED_MODEL from environment with default
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Global state
_vectorstore = None
_embeddings = None
_vector_ok = False

def _get_embeddings():
    """Get or create the embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        print(f"Embedding model: {EMBED_MODEL}")
    return _embeddings

def _load_one(path: Path):
    """Load a single document based on file extension."""
    if path.suffix.lower() in [".md", ".txt"]:
        return TextLoader(str(path), encoding="utf-8").load()
    if path.suffix.lower() == ".pdf":
        return PyPDFLoader(str(path)).load()
    return []

def load_docs(data_dir: str):
    """Load documents from a directory, filtering for supported file types."""
    docs = []
    for p in Path(data_dir).rglob("*.*"):
        docs += _load_one(p)
    return docs

def _splitter():
    """Create text splitter with reasonable chunk size and overlap."""
    return RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=100, 
        separators=["\n\n", "\n", ". ", " "]
    )

def _get_vectorstore():
    """Get Qdrant vectorstore with initialization and caching."""
    global _vectorstore, _vector_ok
    
    if _vectorstore is None:
        print("🔄 Initializing vector store...")
        embeddings = _get_embeddings()
        _vectorstore = init_vector_store(embeddings)
        _vector_ok = _vectorstore is not None
        
        if _vector_ok:
            print("✅ Vector store initialized successfully")
        else:
            print("❌ Vector store initialization failed")
    
    return _vectorstore

def build_vectorstore(data_dir: str):
    """Build vector store from data directory."""
    try:
        vs = _get_vectorstore()
        if vs is None:
            print("⚠️  Vector store not available - skipping build")
            return None
            
        splitter = _splitter()
        chunks = splitter.split_documents(load_docs(data_dir))
        
        # Extract texts and metadatas for add_texts
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Add documents to the vector store
        add_texts(vs, texts, metadatas)
        print(f"Vector store built successfully")
        return vs
    except Exception as e:
        print(f"❌ Vector store build failed: {e}")
        return None

def get_vectorstore():
    """Get existing vector store."""
    try:
        vs = _get_vectorstore()
        if vs is None:
            print("⚠️  Vector store not available - returning None")
            return None
        
        print(f"Vector store loaded successfully")
        return vs
    except Exception as e:
        print(f"❌ Vector store load failed: {e}")
        return None

def retrieve(query: str, k: int = None):
    """Retrieve documents from vector store with telemetry."""
    if k is None:
        k = int(os.getenv("RETRIEVAL_K", "4"))
    
    print(f"🔍 RAG Retrieve - Query: '{query}', k={k}")
    
    vs = get_vectorstore()
    if vs is None:
        print(f"⚠️  Vector store not available - returning empty results for query: '{query[:50]}...'")
        return []
    
    try:
        # Debug: Check if embeddings are available
        if hasattr(vs, 'embeddings') and vs.embeddings is not None:
            print("✅ Vector store has embeddings available")
        elif hasattr(vs, 'embedding_function') and vs.embedding_function is not None:
            print("✅ Vector store has embedding_function available")
        else:
            print("⚠️  Vector store has no embeddings available!")
        
        # Try using retriever first, fallback to similarity_search
        try:
            retriever = vs.as_retriever(search_kwargs={"k": k})
            results = retriever.get_relevant_documents(query)
            print(f"✅ Retrieved {len(results)} documents using retriever")
        except Exception as retriever_error:
            print(f"⚠️  Retriever failed: {retriever_error}, trying similarity_search")
            results = vs.similarity_search(query, k=k)
            print(f"✅ Retrieved {len(results)} documents using similarity_search")
        
        # Debug: Print source paths for debugging
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "unknown")
            content_preview = doc.page_content[:100].replace('\n', ' ')
            print(f"  📄 Doc {i+1}: {source}")
            print(f"      Content: {content_preview}...")
        
        return results
    except Exception as e:
        print(f"❌ Vector store retrieval failed for query: '{query[:50]}...' - {e}")
        return []

def get_document_count():
    """Get document count from vector store."""
    try:
        vs = _get_vectorstore()
        if vs is None:
            return 0
        
        count = vector_count(vs)
        return count
    except Exception as e:
        print(f"⚠️  Could not get document count: {e}")
        return 0

def ingest_data_corpus():
    """Ingest all data from data directory into vector store."""
    data_dir = os.getenv("SEED_DATA_DIR", "./data")
    
    print(f"🔍 Checking data directory: {data_dir}")
    print(f"🔍 Directory exists: {os.path.exists(data_dir)}")
    
    if not os.path.exists(data_dir):
        print(f"⚠️  Data directory not found: {data_dir}")
        return False
    
    try:
        # Load documents from data directory
        docs = load_docs(data_dir)
        print(f"🔍 Found {len(docs)} documents in {data_dir}")
        
        if not docs:
            print(f"⚠️  No documents found in data directory: {data_dir}")
            return False
        
        print(f"📚 Loading {len(docs)} documents from {data_dir}")
        
        # Split documents into chunks
        splitter = _splitter()
        chunks = splitter.split_documents(docs)
        print(f"📝 Split into {len(chunks)} chunks")
        
        # Get vector store and add documents
        vs = _get_vectorstore()
        if vs is None:
            print("⚠️  Vector store not available - skipping ingestion")
            return False
        
        # Extract texts and metadatas for add_texts
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        print(f"🔍 About to add {len(texts)} texts to vector store")
        
        # Add documents to the vector store
        add_texts(vs, texts, metadatas)
        
        print(f"✅ Data corpus ingested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Data corpus ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_vectorstore_with_auto_ingest():
    """Initialize vector store with auto-ingestion if enabled and store is empty."""
    # Check if auto-ingest is enabled
    auto_ingest = os.getenv("AUTO_INGEST", "0").strip() == "1"
    print(f"🔍 Auto-ingest enabled: {auto_ingest}")
    
    # Initialize vector store
    embeddings = _get_embeddings()
    store = init_vector_store(embeddings)
    
    if store is None:
        print("❌ Failed to initialize vector store")
        return
    
    # Get initial document count
    n = vector_count(store)
    print(f"Vector doc count: {n}")
    
    # If store is empty and auto-ingest is enabled, run ingestion
    if n == 0 and auto_ingest:
        print("🔄 Auto-ingesting data corpus (AUTO_INGEST=1)")
        if ingest_data_corpus():
            # Recompute and log the new count
            new_count = vector_count(store)
            print(f"Vector doc count: {new_count}")
        else:
            print("⚠️  Auto-ingest failed, continuing with empty store")
    elif n > 0:
        print(f"✅ Vector store already has {n} documents, skipping auto-ingest")

def is_vectorstore_available():
    """Check if vector store is available and working."""
    global _vector_ok
    return _vector_ok and is_qdrant_available()

def get_vectorstore_info():
    """Get vector store information for health checks."""
    try:
        vs = _get_vectorstore()
        if vs is None:
            return {
                "vector_store": "qdrant",
                "vector_ok": False,
                "vector_docs": 0,
                "vector_collection": "unknown"
            }
        
        collection_name = os.getenv("QDRANT_COLLECTION", "aurora")
        doc_count = get_document_count()
        
        return {
            "vector_store": "qdrant",
            "vector_ok": True,
            "vector_docs": doc_count,
            "vector_collection": collection_name
        }
    except Exception as e:
        print(f"⚠️  Could not get vector store info: {e}")
        return {
            "vector_store": "qdrant",
            "vector_ok": False,
            "vector_docs": 0,
            "vector_collection": "unknown"
        }