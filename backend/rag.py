from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import tempfile

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def _get_chroma_dir():
    """Get ChromaDB directory with fallback to writable path."""
    # Try environment variable first
    chroma_dir = os.getenv("CHROMA_DIR")
    
    if chroma_dir:
        try:
            # Try to create directory and test writability
            os.makedirs(chroma_dir, exist_ok=True)
            
            # Quick write probe
            test_file = os.path.join(chroma_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            
            print(f"✅ Chroma dir: {chroma_dir}")
            return chroma_dir
        except Exception as e:
            print(f"⚠️  CHROMA_DIR {chroma_dir} not writable: {e}")
            print("   Falling back to /tmp/chroma_store")
    
    # Fallback to safe writable path
    fallback_dir = "/tmp/chroma_store"
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        print(f"✅ Chroma dir: {fallback_dir}")
        return fallback_dir
    except Exception as e:
        print(f"❌ Fallback directory creation failed: {e}")
        # Last resort: use system temp directory
        temp_dir = os.path.join(tempfile.gettempdir(), "chroma_store")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"✅ Chroma dir: {temp_dir} (system temp)")
        return temp_dir

# Initialize ChromaDB directory
CHROMA_DIR = _get_chroma_dir()
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

def build_vectorstore(data_dir: str):
    """Build ChromaDB vector store from data directory."""
    try:
        splitter = _splitter()
        chunks = splitter.split_documents(load_docs(data_dir))
        vs = Chroma.from_documents(chunks, _get_embedder(), persist_directory=CHROMA_DIR)
        vs.persist()
        return vs
    except Exception as e:
        print(f"❌ ChromaDB build failed: {e}")
        return None

def get_vectorstore():
    """Get existing ChromaDB vector store."""
    try:
        return Chroma(persist_directory=CHROMA_DIR, embedding_function=_get_embedder())
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
