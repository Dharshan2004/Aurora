'''
EMBEDDING OPERATIONS FOR RAG
'''

from langchain.embeddings import HuggingFaceEmbeddings


# TODO: Change to a more accurate model for production purposes
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2" # For evaluation purposes 


'''
Function to build an embedding model
'''

def build_embedding_model():
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)