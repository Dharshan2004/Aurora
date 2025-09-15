from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Use environment variable for ChromaDB directory, default to /data/chroma_store
CHROMA_DIR = os.getenv("CHROMA_DIR", "/data/chroma_store")
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
    # Ensure ChromaDB directory exists and is writable
    try:
        Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        print(f"✅ ChromaDB directory: {CHROMA_DIR}")
        
        splitter = _splitter()
        chunks = splitter.split_documents(load_docs(data_dir))
        vs = Chroma.from_documents(chunks, _get_embedder(), persist_directory=CHROMA_DIR)
        vs.persist()
        return vs
    except Exception as e:
        error_msg = str(e).lower()
        if "readonly" in error_msg or "read-only" in error_msg or "permission denied" in error_msg:
            print(f"⚠️  ChromaDB directory is read-only: {CHROMA_DIR}")
            print("   This is normal for cloud deployments with restricted access")
            # Return a mock vectorstore that doesn't persist
            return None
        else:
            print(f"❌ ChromaDB initialization failed: {e}")
            raise

def get_vectorstore():
    try:
        return Chroma(persist_directory=CHROMA_DIR, embedding_function=_get_embedder())
    except Exception as e:
        error_msg = str(e).lower()
        if "readonly" in error_msg or "read-only" in error_msg or "permission denied" in error_msg:
            print(f"⚠️  ChromaDB directory is read-only: {CHROMA_DIR}")
            return None
        else:
            raise

def retrieve(query: str, k: int = 6):
    vs = get_vectorstore()
    if vs is None:
        print("⚠️  ChromaDB not available - returning empty results")
        return []
    return vs.similarity_search(query, k=k)
