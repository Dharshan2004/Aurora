"""
Qdrant vector store abstraction for Aurora backend.
Provides a simple interface for Qdrant operations with fallback support.
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

def init_vector_store(embedding) -> Optional[Qdrant]:
    """
    Initialize Qdrant vector store with the given embedding function.
    
    Args:
        embedding: The embedding function (e.g., HuggingFaceEmbeddings)
        
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
        
        # Debug: Print environment variables (without sensitive data)
        print(f"🔍 Environment check:")
        print(f"  QDRANT_URL: {'✅ Set' if qdrant_url else '❌ Not set'}")
        print(f"  QDRANT_API_KEY: {'✅ Set' if qdrant_api_key else '❌ Not set'}")
        print(f"  QDRANT_COLLECTION: {collection_name}")
        
        if not qdrant_url:
            print("❌ QDRANT_URL not configured")
            print("💡 Please set QDRANT_URL environment variable (e.g., https://your-cluster.qdrant.cloud)")
            return None
        
        # Initialize Qdrant client
        client_kwargs = {
            "url": qdrant_url,
            "prefer_grpc": False
        }
        
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        
        client = QdrantClient(**client_kwargs)
        
        # Initialize vector store
        try:
            vector_store = Qdrant(
                client=client,
                collection_name=collection_name,
                embedding_function=embedding
            )
        except Exception as e:
            print(f"⚠️  First attempt failed: {e}")
            # Try alternative parameter name
            try:
                vector_store = Qdrant(
                    client=client,
                    collection_name=collection_name,
                    embeddings=embedding
                )
                print("✅ Used 'embeddings' parameter")
            except Exception as e2:
                print(f"⚠️  Second attempt failed: {e2}")
                # Try without embedding parameter (will use default)
                try:
                    vector_store = Qdrant(
                        client=client,
                        collection_name=collection_name
                    )
                    print("✅ Initialized without embedding parameter")
                except Exception as e3:
                    print(f"❌ All initialization attempts failed: {e3}")
                    return None
        
        # Ensure collection exists
        try:
            # Try to get collection info to check if it exists
            client.get_collection(collection_name)
            print(f"✅ Using existing Qdrant collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            print(f"🔄 Creating Qdrant collection: {collection_name}")
            
            # Get embedding dimension
            try:
                embedding_dim = embedding.client.get_sentence_embedding_dimension()
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
        
        # Get collection info
        collection_info = store.client.get_collection(store.collection_name)
        count = collection_info.vectors_count
        print(f"Vector count: {count}")
        return count
        
    except Exception as e:
        print(f"⚠️  Could not get vector count: {e}")
        return 0

def add_texts(store: Qdrant, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Add texts to the vector store in batches.
    
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
        
        # Add documents in batches
        batch_size = 100  # Reasonable batch size for Qdrant
        total_added = 0
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size] if metadatas else None
            
            store.add_texts(
                texts=batch_texts,
                metadatas=batch_metadatas
            )
            
            total_added += len(batch_texts)
            print(f"📝 Added batch {i//batch_size + 1}: {len(batch_texts)} documents")
        
        print(f"✅ Added {total_added} documents to vector store")
        
    except Exception as e:
        print(f"❌ Failed to add texts to vector store: {e}")

def test_environment():
    """Test function to verify environment variables are accessible."""
    print("🔍 Testing environment variables:")
    
    # Test all Qdrant-related environment variables
    env_vars = [
        "QDRANT_URL",
        "QDRANT_API_KEY", 
        "QDRANT_COLLECTION",
        "AUTO_INGEST",
        "SEED_DATA_DIR",
        "RETRIEVAL_K"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Don't print sensitive values
            if "API_KEY" in var:
                print(f"  {var}: ✅ Set (hidden)")
            else:
                print(f"  {var}: ✅ Set = {value}")
        else:
            print(f"  {var}: ❌ Not set")
    
    # Test if we can access the environment at all
    print(f"  Total env vars: {len(os.environ)}")
    print(f"  Python path: {os.getcwd()}")
    
    return os.getenv("QDRANT_URL") is not None

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
