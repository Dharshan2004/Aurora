'''
CHUNKER OPERATIONS FOR RAG
'''

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pathlib import Path

'''
Function to build a splitter
'''

def build_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "]
    )

''' 
Function to enrich metadata
'''

def enrich_metadata(docs: list[Document]):
    enriched = []
    for d in docs:
        meta = dict(d.metadata)
        src = meta.get("source", "")
        meta["source_type"] = "policy" if "policies" in src else "handbook"
        meta["title"] = Path(src).name
        enriched.append(Document(page_content=d.page_content, metadata=meta))
    return enriched


def chunk_docs(docs: list[Document]):
    splitter = build_splitter()
    return splitter.split_documents(docs)