import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .code_splitter import CodeChunk
from ..core.config import settings


class VectorStoreError(Exception):
    """Custom exception for vector store operations."""
    pass


class VectorStore:
    """
    Vector database service using ChromaDB for storing and querying code embeddings.
    
    Features:
    - Task-specific isolated collections
    - Semantic search over code chunks
    - Automatic embedding generation
    - Collection lifecycle management
    """
    
    def __init__(self):
        """Initialize the ChromaDB client and embedding model."""
        self.client = None
        self.embedding_model = None
        self._initialize_client()
        self._initialize_embedding_model()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with appropriate settings."""
        try:
            # Configure ChromaDB settings
            chroma_settings = Settings(
                persist_directory=settings.chromadb_persist_directory,
                anonymized_telemetry=False
            )
            
            # Create ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.chromadb_persist_directory,
                settings=chroma_settings
            )
            
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize ChromaDB client: {str(e)}")
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model for generating vector representations."""
        try:
            # Use a code-optimized embedding model
            model_name = "microsoft/codebert-base"  # Good for code similarity
            # Fallback to a general model if CodeBERT is not available
            try:
                self.embedding_model = SentenceTransformer(model_name)
            except Exception:
                # Fallback to a smaller general-purpose model
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize embedding model: {str(e)}")
    
    def create_collection(self, task_id: str) -> str:
        """
        Create a new collection for a specific analysis task.
        
        Args:
            task_id: Unique identifier for the analysis task
            
        Returns:
            str: Collection name
            
        Raises:
            VectorStoreError: If collection creation fails
        """
        try:
            collection_name = f"task_{task_id}"
            
            # Delete existing collection if it exists
            try:
                self.client.delete_collection(collection_name)
            except ValueError:
                # Collection doesn't exist, which is fine
                pass
            
            # Create new collection
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"task_id": task_id, "created_at": str(uuid.uuid4())}
            )
            
            return collection_name
            
        except Exception as e:
            raise VectorStoreError(f"Failed to create collection for task {task_id}: {str(e)}")
    
    def delete_collection(self, task_id: str) -> bool:
        """
        Delete the collection for a specific analysis task.
        
        Args:
            task_id: Unique identifier for the analysis task
            
        Returns:
            bool: True if deleted successfully, False if collection didn't exist
            
        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            collection_name = f"task_{task_id}"
            
            try:
                self.client.delete_collection(collection_name)
                return True
            except ValueError:
                # Collection doesn't exist
                return False
                
        except Exception as e:
            raise VectorStoreError(f"Failed to delete collection for task {task_id}: {str(e)}")
    
    def add_chunks(self, task_id: str, chunks: List[CodeChunk]) -> int:
        """
        Add code chunks to the vector database for a specific task.
        
        Args:
            task_id: Unique identifier for the analysis task
            chunks: List of code chunks to add
            
        Returns:
            int: Number of chunks successfully added
            
        Raises:
            VectorStoreError: If adding chunks fails
        """
        try:
            collection_name = f"task_{task_id}"
            
            # Get the collection
            try:
                collection = self.client.get_collection(collection_name)
            except ValueError:
                raise VectorStoreError(f"Collection for task {task_id} does not exist")
            
            if not chunks:
                return 0
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Create unique ID for each chunk
                chunk_id = f"{task_id}_{i}_{hash(chunk.chunk_code) % 10000}"
                
                # Prepare document text (combine code with context for better search)
                document_text = f"File: {chunk.file_path}\n"
                document_text += f"Type: {chunk.chunk_type}\n"
                document_text += f"Context: {chunk.parent_context}\n\n"
                document_text += chunk.chunk_code
                
                documents.append(document_text)
                metadatas.append(chunk.to_dict())
                ids.append(chunk_id)
            
            # Generate embeddings
            embeddings = self._generate_embeddings(documents)
            
            # Add to collection in batches (ChromaDB has limits)
            batch_size = 100
            added_count = 0
            
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids,
                    embeddings=batch_embeddings
                )
                
                added_count += len(batch_docs)
            
            return added_count
            
        except Exception as e:
            raise VectorStoreError(f"Failed to add chunks for task {task_id}: {str(e)}")
    
    def query_similar_code(self, task_id: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query for similar code chunks using semantic search.
        
        Args:
            task_id: Unique identifier for the analysis task
            query_text: Natural language or code query
            n_results: Maximum number of results to return
            
        Returns:
            List[Dict]: List of similar code chunks with metadata and similarity scores
            
        Raises:
            VectorStoreError: If query fails
        """
        try:
            collection_name = f"task_{task_id}"
            
            # Get the collection
            try:
                collection = self.client.get_collection(collection_name)
            except ValueError:
                raise VectorStoreError(f"Collection for task {task_id} does not exist")
            
            # Generate embedding for query
            query_embedding = self._generate_embeddings([query_text])[0]
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 100),  # ChromaDB limit
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                        "chunk_code": results["metadatas"][0][i]["chunk_code"],
                        "file_path": results["metadatas"][0][i]["file_path"],
                        "chunk_type": results["metadatas"][0][i]["chunk_type"],
                        "parent_context": results["metadatas"][0][i]["parent_context"]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            raise VectorStoreError(f"Failed to query similar code for task {task_id}: {str(e)}")
    
    def query_by_filters(self, task_id: str, filters: Dict[str, Any], n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Query code chunks by metadata filters.
        
        Args:
            task_id: Unique identifier for the analysis task
            filters: Dictionary of metadata filters (e.g., {"language": "python", "chunk_type": "function"})
            n_results: Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching code chunks
            
        Raises:
            VectorStoreError: If query fails
        """
        try:
            collection_name = f"task_{task_id}"
            
            # Get the collection
            try:
                collection = self.client.get_collection(collection_name)
            except ValueError:
                raise VectorStoreError(f"Collection for task {task_id} does not exist")
            
            # Convert filters to ChromaDB format
            where_clause = {}
            for key, value in filters.items():
                where_clause[key] = {"$eq": value}
            
            # Query with filters
            results = collection.get(
                where=where_clause,
                limit=n_results,
                include=["documents", "metadatas"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"]:
                for i in range(len(results["documents"])):
                    result = {
                        "document": results["documents"][i],
                        "metadata": results["metadatas"][i],
                        "chunk_code": results["metadatas"][i]["chunk_code"],
                        "file_path": results["metadatas"][i]["file_path"],
                        "chunk_type": results["metadatas"][i]["chunk_type"],
                        "parent_context": results["metadatas"][i]["parent_context"]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            raise VectorStoreError(f"Failed to query by filters for task {task_id}: {str(e)}")
    
    def get_collection_stats(self, task_id: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            task_id: Unique identifier for the analysis task
            
        Returns:
            Dict: Collection statistics
            
        Raises:
            VectorStoreError: If getting stats fails
        """
        try:
            collection_name = f"task_{task_id}"
            
            # Get the collection
            try:
                collection = self.client.get_collection(collection_name)
            except ValueError:
                raise VectorStoreError(f"Collection for task {task_id} does not exist")
            
            # Get basic stats
            count = collection.count()
            
            # Get language distribution
            all_items = collection.get(include=["metadatas"])
            language_counts = {}
            chunk_type_counts = {}
            
            for metadata in all_items["metadatas"]:
                lang = metadata.get("language", "unknown")
                chunk_type = metadata.get("chunk_type", "unknown")
                
                language_counts[lang] = language_counts.get(lang, 0) + 1
                chunk_type_counts[chunk_type] = chunk_type_counts.get(chunk_type, 0) + 1
            
            return {
                "total_chunks": count,
                "languages": language_counts,
                "chunk_types": chunk_type_counts,
                "collection_name": collection_name
            }
            
        except Exception as e:
            raise VectorStoreError(f"Failed to get collection stats for task {task_id}: {str(e)}")
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            raise VectorStoreError(f"Failed to generate embeddings: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the vector store.
        
        Returns:
            Dict: Health status information
        """
        try:
            # Test basic operations
            test_collection_name = "health_check_test"
            
            # Clean up any existing test collection
            try:
                self.client.delete_collection(test_collection_name)
            except ValueError:
                pass
            
            # Create test collection
            collection = self.client.create_collection(test_collection_name)
            
            # Test adding a document
            test_doc = ["print('Hello, World!')"]
            test_metadata = [{"test": True}]
            test_id = ["test_id"]
            test_embedding = self._generate_embeddings(test_doc)
            
            collection.add(
                documents=test_doc,
                metadatas=test_metadata,
                ids=test_id,
                embeddings=test_embedding
            )
            
            # Test querying
            results = collection.query(
                query_embeddings=[test_embedding[0]],
                n_results=1
            )
            
            # Clean up
            self.client.delete_collection(test_collection_name)
            
            return {
                "status": "healthy",
                "client_initialized": self.client is not None,
                "embedding_model_initialized": self.embedding_model is not None,
                "test_operations_successful": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "client_initialized": self.client is not None,
                "embedding_model_initialized": self.embedding_model is not None,
                "test_operations_successful": False
            } 