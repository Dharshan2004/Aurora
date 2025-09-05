'''
VECTOR STORE OPERATIONS FOR RAG
'''

# rag/vector_store.py  (patched)

from langchain.vectorstores import Chroma
from pathlib import Path
from .embeddings import build_embedding_model
from .chunkers import chunk_docs, enrich_metadata
from .loaders import load_docs
from ..config import CHROMA_PERSIST_DIR   # <-- keep this

# -- Build Vector Store --
def build_vectorstore(data_dir: str):
    embedding_model = build_embedding_model()
    raw_docs = load_docs(data_dir)
    docs = enrich_metadata(raw_docs)
    docs = chunk_docs(docs)
    vs = Chroma.from_documents(docs, embedding_model, persist_directory=CHROMA_PERSIST_DIR)  # <-- fix
    vs.persist()
    return vs

def get_vectorstore():
    embedding_model = build_embedding_model()
    return Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_model)  # <-- fix

def retrieve(question: str, k: int = 4):
    vs = get_vectorstore()
    # similarity search with scores gives [(Document, score), ...]
    results = vs.similarity_search_with_score(question, k=k)
    # normalize into {content, metadata, score}
    retrieved = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(1.0 - min(max(score, 0.0), 1.0)) if isinstance(score, float) else None  # optional
        }
        for (doc, score) in results
    ]
    # compact citations for UI
    citations = [
        {
            "source": r["metadata"].get("source") or r["metadata"].get("path") or "unknown",
            "page": r["metadata"].get("page"),
            "score": r["score"]
        }
        for r in retrieved
    ]
    return retrieved, citations