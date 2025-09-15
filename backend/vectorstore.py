"""
Qdrant vector store abstraction for Aurora backend.
Provides a simple interface for Qdrant operations with proper embedding initialization.
"""

import os
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Try preferred import first, fallback to community
try:
    from langchain_qdrant import Qdrant
    QDRANT_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.vectorstores import Qdrant
        QDRANT_AVAILABLE = True
    except ImportError:
        QDRANT_AVAILABLE = False
        Qdrant = None

def init_vector_store(embeddings) -> Optional[Qdrant]:
    """
    Initialize Qdrant vector store with the given embedding function.
    
    Args:
        embeddings: The embedding function (e.g., HuggingFaceEmbeddings)
        
    Returns:
        Qdrant vector store instance or None if initialization fails
    """
    if not QDRANT_AVAILABLE:
        print("❌ Qdrant dependencies not available")
        return None
    
    try:
        # Get configuration from environment
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("QDRANT_COLLECTION", "aurora")
        
        if not qdrant_url:
            print("❌ QDRANT_URL not configured")
            return None
        
        # Initialize Qdrant client
        client_kwargs = {
            "url": qdrant_url,
            "prefer_grpc": False
        }
        
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        
        client = QdrantClient(**client_kwargs)
        
        # Ensure collection exists with dimension inference
        try:
            # Try to get collection info to check if it exists
            client.get_collection(collection_name)
            print(f"✅ Using existing Qdrant collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            print(f"🔄 Creating Qdrant collection: {collection_name}")
            
            # Get embedding dimension
            try:
                test_embedding = embeddings.embed_query("dimension probe")
                embedding_dim = len(test_embedding)
                print(f"📏 Embedding dimension: {embedding_dim}")
            except Exception as e:
                print(f"⚠️  Could not get embedding dimension: {e}")
                # Fallback to common dimension for sentence-transformers
                embedding_dim = 384  # Default for all-MiniLM-L6-v2
                print(f"📏 Using fallback embedding dimension: {embedding_dim}")
            
            # Create collection with cosine distance
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_dim,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✅ Created Qdrant collection: {collection_name}")
        
        # Initialize vector store with embeddings
        vector_store = None
        
        # Try different initialization methods
        init_methods = [
            ("embeddings", lambda: Qdrant(client=client, collection_name=collection_name, embeddings=embeddings)),
            ("embedding", lambda: Qdrant(client=client, collection_name=collection_name, embedding=embeddings)),
        ]
        
        for method_name, init_func in init_methods:
            try:
                vector_store = init_func()
                print(f"✅ Initialized with '{method_name}' parameter")
                break
            except Exception as e:
                print(f"⚠️  {method_name} method failed: {e}")
                continue
        
        if vector_store is None:
            print("❌ All initialization methods failed")
            return None
        
        print(f"Vector store: qdrant • collection={collection_name}")
        
        return vector_store
        
    except Exception as e:
        print(f"❌ Qdrant initialization failed: {e}")
        return None

def vector_count(store: Qdrant) -> int:
    """
    Get the number of vectors in the store.
    
    Args:
        store: Qdrant vector store instance
        
    Returns:
        Number of vectors in the collection
    """
    try:
        if store is None:
            return 0
        
        # Use client.count for robust counting
        try:
            result = store.client.count(store.collection_name, exact=True)
            count = result.count
            return count
        except Exception:
            # Fallback to collection info
            collection_info = store.client.get_collection(store.collection_name)
            if hasattr(collection_info, 'vectors_count'):
                return collection_info.vectors_count
            elif hasattr(collection_info, 'points_count'):
                return collection_info.points_count
            elif hasattr(collection_info, 'status') and hasattr(collection_info.status, 'vectors_count'):
                return collection_info.status.vectors_count
            else:
                return 0
        
    except Exception as e:
        print(f"❌ Could not get vector count: {e}")
        return 0

def add_texts(store: Qdrant, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Add texts to the vector store.
    
    Args:
        store: Qdrant vector store instance
        texts: List of text documents to add
        metadatas: Optional list of metadata dictionaries
    """
    try:
        if store is None:
            print("⚠️  Vector store not available - skipping add_texts")
            return
        
        if not texts:
            print("⚠️  No texts to add")
            return
        
        # Ensure metadatas is properly formatted
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Add documents in batches
        batch_size = 100  # Reasonable batch size for Qdrant
        total_added = 0
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            
            store.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas
            )
            
            total_added += len(batch_texts)
            print(f"📝 Added batch {i//batch_size + 1}: {len(batch_texts)} documents")
        
        print(f"✅ Added {total_added} documents to vector store")
        
    except Exception as e:
        print(f"❌ Failed to add texts to vector store: {e}")

def is_qdrant_available() -> bool:
    """
    Check if Qdrant is available and properly configured.
    
    Returns:
        True if Qdrant is available and configured, False otherwise
    """
    if not QDRANT_AVAILABLE:
        return False
    
    qdrant_url = os.getenv("QDRANT_URL")
    return qdrant_url is not None