from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DB_DIR = str((Path(__file__).resolve().parent.parent / "chroma_db"))
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
    splitter = _splitter()
    chunks = splitter.split_documents(load_docs(data_dir))
    vs = Chroma.from_documents(chunks, _get_embedder(), persist_directory=DB_DIR)
    vs.persist()
    return vs

def get_vectorstore():
    return Chroma(persist_directory=DB_DIR, embedding_function=_get_embedder())

def retrieve(query: str, k: int = 6):
    return get_vectorstore().similarity_search(query, k=k)
