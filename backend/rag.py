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
    
    # Check for reset flag
    reset_chroma = os.getenv("CHROMA_RESET", "").lower() in {"1", "true"}
    
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
        """Reset directory contents if reset flag is set."""
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
    """Retrieve documents from ChromaDB."""
    vs = get_vectorstore()
    if vs is None:
        print("⚠️  ChromaDB not available - returning empty results")
        return []
    return vs.similarity_search(query, k=k)

def is_chroma_available():
    """Check if ChromaDB is available."""
    return _get_chroma_client() is not None
