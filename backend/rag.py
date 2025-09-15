from pathlib import Path
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import os
import tempfile
import time
import shutil

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Single source of truth for ChromaDB path
CHROMA_DIR = os.getenv("CHROMA_DIR", "/data/chroma_store")
os.makedirs(CHROMA_DIR, exist_ok=True)
print(f"Chroma dir: {CHROMA_DIR}")

# Global state
_vectorstore = None
_embedder = None
_chroma_ok = False

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

def _get_chroma_vectorstore():
    """Get ChromaDB vectorstore with legacy API and self-healing."""
    global _vectorstore, _chroma_ok, CHROMA_DIR
    
    if _vectorstore is None:
        def _try_init_chroma(path):
            """Try to initialize ChromaDB vectorstore with given path."""
            try:
                # Check for CHROMA_RESET=1
                if os.getenv("CHROMA_RESET", "0").strip() == "1":
                    print(f"🔄 CHROMA_RESET=1 detected, cleaning directory: {path}")
                    if os.path.exists(path):
                        shutil.rmtree(path, ignore_errors=True)
                    os.makedirs(path, exist_ok=True)
                
                # Use legacy Chroma API with persist_directory
                embedder = _get_embedder()
                collection_name = os.getenv("CHROMA_COLLECTION", "aurora")
                vs = Chroma(
                    persist_directory=path,
                    collection_name=collection_name,
                    embedding_function=embedder
                )
                print(f"Chroma backend: legacy SQLite")
                print(f"Chroma dir: {path}")
                return vs
            except Exception as e:
                error_msg = str(e).lower()
                if "deprecated configuration" in error_msg or "readonly database" in error_msg:
                    print(f"⚠️  ChromaDB error: {e}")
                    return None
                else:
                    print(f"❌ ChromaDB vectorstore init failed: {e}")
                    return None
        
        # Try to initialize with current path
        _vectorstore = _try_init_chroma(CHROMA_DIR)
        
        # If error, try force clean
        if _vectorstore is None:
            force_clean = os.getenv("CHROMA_FORCE_CLEAN", "").lower() in {"1", "true"}
            if force_clean:
                print(f"🔄 Force cleaning ChromaDB directory: {CHROMA_DIR}")
                try:
                    if os.path.exists(CHROMA_DIR):
                        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
                    os.makedirs(CHROMA_DIR, exist_ok=True)
                    _vectorstore = _try_init_chroma(CHROMA_DIR)
                except Exception as e:
                    print(f"⚠️  Force clean failed: {e}")
            
            # If still failing, fallback to timestamped directory
            if _vectorstore is None:
                fallback_dir = f"/tmp/chroma_store/{int(time.time())}"
                print(f"🔄 Falling back to: {fallback_dir}")
                os.makedirs(fallback_dir, exist_ok=True)
                CHROMA_DIR = fallback_dir  # Update global path
                _vectorstore = _try_init_chroma(fallback_dir)
        
        # Set success flag
        _chroma_ok = _vectorstore is not None
    
    return _vectorstore

def build_vectorstore(data_dir: str):
    """Build ChromaDB vector store from data directory."""
    try:
        vs = _get_chroma_vectorstore()
        if vs is None:
            print("⚠️  ChromaDB vectorstore not available - skipping build")
            return None
            
        splitter = _splitter()
        chunks = splitter.split_documents(load_docs(data_dir))
        
        # Add documents to the existing vectorstore
        vs.add_documents(chunks)
        print(f"ChromaDB vector store built successfully")
        return vs
    except Exception as e:
        print(f"❌ ChromaDB build failed: {e}")
        return None

def get_vectorstore():
    """Get existing ChromaDB vector store."""
    try:
        vs = _get_chroma_vectorstore()
        if vs is None:
            print("⚠️  ChromaDB vectorstore not available - returning None")
            return None
        
        print(f"ChromaDB vector store loaded successfully")
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
    """Get document count using the legacy Chroma API."""
    try:
        vs = _get_chroma_vectorstore()
        if vs is None:
            return 0
        
        # Get document count using legacy API
        # This is a best-effort approach since legacy API doesn't have direct count
        try:
            # Try to get all documents and count them
            results = vs.similarity_search("", k=10000)  # Large k to get all docs
            count = len(results)
            print(f"Chroma doc count: {count}")
            return count
        except Exception:
            # If that fails, try to access the underlying collection
            try:
                collection = vs._collection
                count = collection.count()
                print(f"Chroma doc count: {count}")
                return count
            except Exception:
                print(f"⚠️  Could not get document count using legacy API")
                return 0
    except Exception as e:
        print(f"⚠️  Could not get document count: {e}")
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
        
        # Get ChromaDB vectorstore and add documents
        vs = _get_chroma_vectorstore()
        if vs is None:
            print("⚠️  ChromaDB vectorstore not available - skipping ingestion")
            return False
        
        # Add documents to the existing vectorstore
        vs.add_documents(chunks)
        
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
            global _vectorstore
            _vectorstore = None  # Force re-initialization
            new_count = get_document_count()
            print(f"📊 Chroma doc count after auto-ingest: {new_count}")
        else:
            print("⚠️  Auto-ingest failed, continuing with empty store")
    
def is_chroma_available():
    """Check if ChromaDB is available and working."""
    global _chroma_ok
    return _chroma_ok
