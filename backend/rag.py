from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from chromadb import PersistentClient
from chromadb.config import Settings
import os
import tempfile
import time
import shutil

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Single source of truth for ChromaDB path
CHROMA_DIR = os.getenv("CHROMA_DIR", "/tmp/chroma_store")
os.makedirs(CHROMA_DIR, exist_ok=True)

# Global state
_chroma_client = None
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

def _get_chroma_client():
    """Get ChromaDB client with new client pattern and self-healing."""
    global _chroma_client, _chroma_ok, CHROMA_DIR
    
    if _chroma_client is None:
        def _try_init_chroma(path):
            """Try to initialize ChromaDB client with given path."""
            try:
                # Create client with duckdb+parquet backend
                client = PersistentClient(
                    path=path,
                    settings=Settings(chroma_db_impl="duckdb+parquet", anonymized_telemetry=False)
                )
                print(f"Chroma backend: duckdb+parquet")
                print(f"Chroma dir: {path}")
                return client
            except Exception as e:
                error_msg = str(e).lower()
                if "deprecated configuration" in error_msg or "readonly database" in error_msg:
                    print(f"⚠️  ChromaDB error: {e}")
                    return None
                else:
                    print(f"❌ ChromaDB client init failed: {e}")
                    return None
        
        # Try to initialize with current path
        _chroma_client = _try_init_chroma(CHROMA_DIR)
        
        # If error, try force clean
        if _chroma_client is None:
            force_clean = os.getenv("CHROMA_FORCE_CLEAN", "").lower() in {"1", "true"}
            if force_clean:
                print(f"🔄 Force cleaning ChromaDB directory: {CHROMA_DIR}")
                try:
                    if os.path.exists(CHROMA_DIR):
                        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
                    os.makedirs(CHROMA_DIR, exist_ok=True)
                    _chroma_client = _try_init_chroma(CHROMA_DIR)
                except Exception as e:
                    print(f"⚠️  Force clean failed: {e}")
            
            # If still failing, fallback to timestamped directory
            if _chroma_client is None:
                fallback_dir = f"/tmp/chroma_store/{int(time.time())}"
                print(f"🔄 Falling back to: {fallback_dir}")
                os.makedirs(fallback_dir, exist_ok=True)
                CHROMA_DIR = fallback_dir  # Update global path
                _chroma_client = _try_init_chroma(fallback_dir)
        
        # Set success flag
        _chroma_ok = _chroma_client is not None
    
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
        
        # Use new client pattern without persist_directory
        collection_name = os.getenv("CHROMA_COLLECTION", "aurora")
        vs = Chroma(client=client, collection_name=collection_name, embedding_function=_get_embedder())
        
        # Add documents to the collection
        vs.add_documents(chunks)
        print(f"ChromaDB vector store built successfully")
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
        
        # Use new client pattern without persist_directory
        collection_name = os.getenv("CHROMA_COLLECTION", "aurora")
        vs = Chroma(client=client, collection_name=collection_name, embedding_function=_get_embedder())
        
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
    """Get document count using the most reliable method."""
    try:
        client = _get_chroma_client()
        if client is None:
            return 0
        
        # Get the collection
        collection_name = os.getenv("CHROMA_COLLECTION", "aurora")
        collection = client.get_collection(collection_name)
        count = collection.count()
        print(f"Chroma doc count: {count}")
        return count
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
        
        # Get ChromaDB client and add documents
        client = _get_chroma_client()
        if client is None:
            print("⚠️  ChromaDB client not available - skipping ingestion")
            return False
        
        collection_name = os.getenv("CHROMA_COLLECTION", "aurora")
        vs = Chroma(client=client, collection_name=collection_name, embedding_function=_get_embedder())
        
        # Add documents to the collection
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
            global _chroma_client
            _chroma_client = None  # Force re-initialization
            new_count = get_document_count()
            print(f"📊 Chroma doc count after auto-ingest: {new_count}")
        else:
            print("⚠️  Auto-ingest failed, continuing with empty store")
    
def is_chroma_available():
    """Check if ChromaDB is available and working."""
    global _chroma_ok
    return _chroma_ok
