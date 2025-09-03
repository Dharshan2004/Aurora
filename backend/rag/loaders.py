'''
LOADERS FOR RAG
'''
from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader

'''
Function to load a single document
'''

def load_doc(path: Path):
    if path.suffix.lower() == ".md":
        return TextLoader(str(path)).load()
    elif path.suffix.lower() == ".pdf":
        return PyPDFLoader(str(path)).load()
    else:
        return []

'''
Function to load all documents in a directory
'''

def load_docs(data_dir: Path):
    docs = []
    for p in Path(data_dir).rglob("*.*"):
        docs += load_doc(p)
    return docs

