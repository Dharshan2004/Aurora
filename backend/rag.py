from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from vectorstore import init_vector_store, vector_count, add_texts, is_qdrant_available
import os
import time

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Global state
_vectorstore = None
_embedder = None
_vector_ok = False

def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embedder

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
        embedder = _get_embedder()
        _vectorstore = init_vector_store(embedder)
        _vector_ok = _vectorstore is not None
    
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
    
    vs = get_vectorstore()
    if vs is None:
        print(f"⚠️  Vector store not available - returning empty results for query: '{query[:50]}...'")
        return []
    
    try:
        # Create retriever with search parameters
        retriever = vs.as_retriever(search_kwargs={"k": k})
        results = retriever.get_relevant_documents(query)
        print(f"🔍 Retrieved {len(results)} documents for query: '{query[:50]}...'")
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

def ingest_seed_corpus():
    """Ingest seed data from SEED_DATA_DIR into vector store."""
    seed_dir = os.getenv("SEED_DATA_DIR", "./data/seed")
    
    if not os.path.exists(seed_dir):
        print(f"⚠️  Seed data directory not found: {seed_dir}")
        return False
    
    try:
        # Load documents from seed directory
        docs = load_docs(seed_dir)
        if not docs:
            print(f"⚠️  No documents found in seed directory: {seed_dir}")
            return False
        
        print(f"📚 Loading {len(docs)} documents from {seed_dir}")
        
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
        
        # Add documents to the vector store
        add_texts(vs, texts, metadatas)
        
        print(f"✅ Seed corpus ingested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Seed corpus ingestion failed: {e}")
        return False

def initialize_vectorstore_with_auto_ingest():
    """Initialize vector store with auto-ingestion if enabled and store is empty."""
    # Test environment variables first
    from vectorstore import test_environment
    test_environment()
    
    # Check if auto-ingest is enabled
    auto_ingest = os.getenv("AUTO_INGEST", "0").strip() == "1"
    
    # Get initial document count
    doc_count = get_document_count()
    print(f"📊 Vector doc count: {doc_count}")
    
    # If store is empty and auto-ingest is enabled, run ingestion
    if doc_count == 0 and auto_ingest:
        print("🔄 Auto-ingesting seed corpus (AUTO_INGEST=1)")
        if ingest_seed_corpus():
            # Re-open vector store and get new count
            global _vectorstore
            _vectorstore = None  # Force re-initialization
            new_count = get_document_count()
            print(f"📊 Vector doc count after auto-ingest: {new_count}")
        else:
            print("⚠️  Auto-ingest failed, continuing with empty store")

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