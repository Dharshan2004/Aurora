'''
VECTOR STORE OPERATIONS FOR RAG
'''

from langchain.vectorstores import Chroma
from pathlib import Path
from .embeddings import build_embedding_model
from .chunkers import chunk_docs, enrich_metadata
from .loaders import load_docs

DB_DIR = str((Path(__file__).resolve().parent.parent / "chroma_db"))

'''
Function to build a vector store
'''

def build_vectorstore(data_dir: str):
    embedding_model = build_embedding_model()
    raw_docs = load_docs(data_dir)
    docs = enrich_metadata(raw_docs)
    docs = chunk_docs(docs)
    vectorstore = Chroma.from_documents(docs, embedding_model, persist_directory=DB_DIR)
    vectorstore.persist()
    return vectorstore

def get_vectorstore():
    embedding_model = build_embedding_model()
    return Chroma(persist_directory=DB_DIR, embedding_function=embedding_model)