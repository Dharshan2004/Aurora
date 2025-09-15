from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import tempfile
import time
import shutil

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def _get_chroma_dir():
    """Get ChromaDB directory with fallback to writable path."""
    # Read CHROMA_DIR from environment
    chroma_dir = os.getenv("CHROMA_DIR", "/tmp/chroma_store")
    
    # Check for reset flag - only reset if explicitly set to 1
    reset_chroma = os.getenv("CHROMA_RESET", "").strip() == "1"
    
    def _test_writability(path):
        """Test if directory is writable."""
        try:
            os.makedirs(path, exist_ok=True)
            # Write probe
            test_file = os.path.join(path, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception:
            return False
    
    def _reset_directory(path):
        """Reset directory contents only if CHROMA_RESET=1."""
        if reset_chroma:
            try:
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)
                os.makedirs(path, exist_ok=True)
                print(f"🔄 ChromaDB reset: cleared {path}")
                return True
            except Exception as e:
                print(f"⚠️  ChromaDB reset failed: {e}")
                return False
        return True
    
    # Try configured directory first
    if _test_writability(chroma_dir):
        if _reset_directory(chroma_dir):
            print(f"✅ Chroma dir: {chroma_dir} (writable: yes)")
            return chroma_dir
        else:
            print(f"⚠️  Chroma dir: {chroma_dir} (writable: yes, reset failed)")
            return chroma_dir
    
    # Fallback to timestamped directory
    print(f"⚠️  CHROMA_DIR {chroma_dir} not writable, falling back to /tmp/chroma_store/<timestamp>")
    fallback_dir = f"/tmp/chroma_store/{int(time.time())}"
    
    if _test_writability(fallback_dir):
        print(f"✅ Chroma dir: {fallback_dir} (writable: yes)")
        return fallback_dir
    
    # Last resort: system temp directory
    temp_dir = os.path.join(tempfile.gettempdir(), f"chroma_store_{int(time.time())}")
    os.makedirs(temp_dir, exist_ok=True)
    print(f"✅ Chroma dir: {temp_dir} (writable: yes, system temp)")
    return temp_dir

# Initialize ChromaDB directory
CHROMA_DIR = _get_chroma_dir()
_chroma_client = None
_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embedder

def _load_one(path: Path):
    if path.suffix.lower() in [".md", ".txt", ".csv"]:
        return TextLoader(str(path), encoding="utf-8").load()
    if path.suffix.lower() == ".pdf":
        return PyPDFLoader(str(path)).load()
    return []

def load_docs(data_dir: str):
    docs = []
    for p in Path(data_dir).rglob("*.*"):
        docs += _load_one(p)
    return docs

def _splitter():
    return RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100, separators=["\n\n","\n",". "," "])

def _get_chroma_client():
    """Get ChromaDB client with proper error handling."""
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
            print(f"✅ ChromaDB client initialized successfully")
            return _chroma_client
        except Exception as e:
            print(f"❌ ChromaDB client init failed: {e}")
            return None
    return _chroma_client

def build_vectorstore(data_dir: str):
    """Build ChromaDB vector store from data directory."""
    try:
        client = _get_chroma_client()
        if client is None:
            print("⚠️  ChromaDB client not available - skipping build")
            return None
            
        splitter = _splitter()
        chunks = splitter.split_documents(load_docs(data_dir))
        vs = Chroma.from_documents(chunks, _get_embedder(), persist_directory=CHROMA_DIR)
        vs.persist()
        print(f"✅ ChromaDB vector store built successfully")
        return vs
    except Exception as e:
        print(f"❌ ChromaDB build failed: {e}")
        return None

def get_vectorstore():
    """Get existing ChromaDB vector store."""
    try:
        client = _get_chroma_client()
        if client is None:
            print("⚠️  ChromaDB client not available - returning None")
            return None
            
        vs = Chroma(persist_directory=CHROMA_DIR, embedding_function=_get_embedder())
        print(f"✅ ChromaDB vector store loaded successfully")
        return vs
    except Exception as e:
        print(f"❌ ChromaDB load failed: {e}")
        return None

def retrieve(query: str, k: int = 6):
    """Retrieve documents from ChromaDB with telemetry."""
    vs = get_vectorstore()
    if vs is None:
        print(f"⚠️  ChromaDB not available - returning empty results for query: '{query[:50]}...'")
        return []
    
    try:
        results = vs.similarity_search(query, k=k)
        print(f"🔍 Retrieved {len(results)} documents for query: '{query[:50]}...'")
        return results
    except Exception as e:
        print(f"❌ ChromaDB retrieval failed for query: '{query[:50]}...' - {e}")
        return []

def get_document_count():
    """Get the number of documents in the ChromaDB store."""
    try:
        vs = get_vectorstore()
        if vs is None:
            return 0
        
        # Try to get count from the underlying collection
        if hasattr(vs, '_collection') and hasattr(vs._collection, 'count'):
            return vs._collection.count()
        
        # Fallback: try to get count from langchain interface
        if hasattr(vs, 'similarity_search'):
            # This is a rough estimate - try a broad search
            try:
                results = vs.similarity_search("", k=1000)  # Get up to 1000 docs
                return len(results)
            except:
                return 0
        
        return 0
    except Exception as e:
        print(f"⚠️  Error getting document count: {e}")
        return 0

def ingest_seed_corpus():
    """Ingest seed data from SEED_DATA_DIR into ChromaDB."""
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
        
        # Create vector store and persist
        vs = Chroma.from_documents(chunks, _get_embedder(), persist_directory=CHROMA_DIR)
        vs.persist()
        
        print(f"✅ Seed corpus ingested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Seed corpus ingestion failed: {e}")
        return False

def initialize_chroma_with_auto_ingest():
    """Initialize ChromaDB with auto-ingestion if enabled and store is empty."""
    # Check if auto-ingest is enabled
    auto_ingest = os.getenv("CHROMA_AUTO_INGEST", "0").strip() == "1"
    
    # Get initial document count
    doc_count = get_document_count()
    print(f"📊 Chroma doc count: {doc_count}")
    
    # If store is empty and auto-ingest is enabled, run ingestion
    if doc_count == 0 and auto_ingest:
        print("🔄 Auto-ingesting seed corpus (CHROMA_AUTO_INGEST=1)")
        if ingest_seed_corpus():
            # Re-open vector store and get new count
            global _chroma_client
            _chroma_client = None  # Force re-initialization
            new_count = get_document_count()
            print(f"📊 Chroma doc count after auto-ingest: {new_count}")
        else:
            print("⚠️  Auto-ingest failed, continuing with empty store")
    
    return doc_count
