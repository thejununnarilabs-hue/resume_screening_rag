"""ChromaDB management for storing and retrieving resume embeddings."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import gc
import shutil

import chromadb


class ChromaManager:
    """Manages ChromaDB collections and operations."""

    def __init__(
        self,
        db_path: str = "data/chroma_db",
        collection_name: str = "resumes"
    ):
        self.db_path = Path(db_path)
        self.collection_name = collection_name

        self.db_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.client = chromadb.PersistentClient(
            path=str(self.db_path)
        )

        self.collection = None

    def create_collection(
        self,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Create a new collection or get existing one.
        """
        try:
            collection_name = name or self.collection_name

            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata or {
                    "description": "Resume embeddings"
                }
            )

            return True

        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add chunks to the collection.
        
        Args:
            chunks: List of chunks with 'id', 'text', 'embedding', 'metadata'
            
        Returns:
            True if successful
        """
        try:
            if not self.collection:
                self.create_collection()
            
            # Prepare data for ChromaDB
            ids = [str(chunk['metadata'].get('candidate_name', '') + 
                       '_' + str(chunk.get('id', ''))) for chunk in chunks]
            embeddings = [chunk['embedding'] for chunk in chunks]
            documents = [chunk['text'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            return True
        except Exception as e:
            print(f"Error adding chunks: {e}")
            return False
    
    def search(self, query_embedding: List[float], n_results: int = 5,
              where: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search collection by embedding.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Filter conditions
            
        Returns:
            Search results from ChromaDB
        """
        try:
            if not self.collection:
                return {'error': 'Collection not initialized'}
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            return results
        except Exception as e:
            print(f"Error searching: {e}")
            return {'error': str(e)}
    
    def search_text(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search by text (requires embedding model).
        
        Args:
            query_text: Text to search for
            n_results: Number of results
            
        Returns:
            Search results
        """
        # This would require the embedding model to be passed or shared
        # For now, this is a placeholder
        pass
    
    def get_by_metadata(self, where: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get chunks by metadata filters.
        
        Args:
            where: Metadata filter conditions
            
        Returns:
            Matching results
        """
        try:
            if not self.collection:
                return {'error': 'Collection not initialized'}
            
            results = self.collection.get(where=where)
            return results
        except Exception as e:
            print(f"Error getting by metadata: {e}")
            return {'error': str(e)}
    
    def get_candidate_chunks(self, candidate_name: str) -> Dict[str, Any]:
        """
        Get all chunks for a specific candidate.
        
        Args:
            candidate_name: Name of candidate
            
        Returns:
            All chunks for candidate
        """
        return self.get_by_metadata({
            'candidate_name': candidate_name
        })
    
    def delete_candidate_data(self, candidate_name: str) -> bool:
        """
        Delete all data for a candidate.
        
        Args:
            candidate_name: Name of candidate
            
        Returns:
            True if successful
        """
        try:
            if not self.collection:
                return False
            
            # Get all chunks for candidate
            results = self.get_candidate_chunks(candidate_name)
            
            # Delete them
            if results.get('ids'):
                self.collection.delete(ids=results['ids'])
            
            return True
        except Exception as e:
            print(f"Error deleting candidate data: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """
        Clear all data in collection.
        
        Returns:
            True if successful
        """
        try:
            if self.collection:
                self.client.delete_collection(name=self.collection.name)
            self.collection = None
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False

    def clear_database(self) -> bool:
        """Clear the collection and remove this temporary ChromaDB directory."""
        collection_cleared = self.clear_collection()
        try:
            self.collection = None
            self.client = None
            gc.collect()
            if self.db_path.exists():
                shutil.rmtree(self.db_path, ignore_errors=True)
            return collection_cleared
        except Exception as e:
            print(f"Error clearing ChromaDB directory: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            if not self.collection:
                return {'error': 'Collection not initialized'}
            
            results = self.collection.get()
            
            return {
                'total_documents': len(results.get('documents', [])),
                'collection_name': self.collection.name,
                'ids_count': len(results.get('ids', []))
            }
        except Exception as e:
            return {'error': str(e)}
