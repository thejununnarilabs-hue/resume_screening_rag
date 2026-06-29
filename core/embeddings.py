"""Embeddings generation using BAAI/bge-base-en-v1.5 model."""

from typing import List, Dict, Any, Optional
import numpy as np


class EmbeddingModel:
    """Wrapper for BAAI/bge-base-en-v1.5 embedding model."""
    
    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model and tokenizer."""
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print(f"Successfully loaded {self.model_name}")
        except ImportError:
            print("Error: sentence-transformers library not found")
            raise
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def encode_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Encode single text to embedding.
        
        Args:
            text: Text to encode
            normalize: Whether to normalize the embedding
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        return embedding
    
    def encode_texts(self, texts: List[str], normalize: bool = True,
                    batch_size: int = 32) -> np.ndarray:
        """
        Encode multiple texts to embeddings.
        
        Args:
            texts: List of texts to encode
            normalize: Whether to normalize embeddings
            batch_size: Batch size for encoding
            
        Returns:
            Array of embeddings (shape: [n_texts, embedding_dim])
        """
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            batch_size=batch_size,
            show_progress_bar=True
        )
        return embeddings
    
    def encode_chunks(self, chunks: List[Dict[str, Any]],
                     batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Encode list of chunk objects.
        
        Args:
            chunks: List of chunk dictionaries with 'text' key
            batch_size: Batch size for encoding
            
        Returns:
            Chunks with added 'embedding' key
        """
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.encode_texts(texts, normalize=True, batch_size=batch_size)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()  # Convert to list for JSON serialization
        
        return chunks
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1 (1 = identical)
        """
        # Ensure numpy arrays
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)
        
        # Normalize
        embedding1 = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        embedding2 = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        
        # Calculate cosine similarity
        return float(np.dot(embedding1, embedding2))
    
    def rank_by_similarity(self, query_embedding: np.ndarray,
                          embeddings_list: List[np.ndarray]) -> List[tuple]:
        """
        Rank embeddings by similarity to query.
        
        Args:
            query_embedding: Query embedding vector
            embeddings_list: List of embeddings to rank
            
        Returns:
            List of (index, similarity_score) tuples, sorted by score (descending)
        """
        scores = []
        for i, emb in enumerate(embeddings_list):
            score = self.similarity(query_embedding, emb)
            scores.append((i, score))
        
        # Sort by score (descending)
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.model:
            return {'error': 'Model not initialized'}
        
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'max_seq_length': self.model.get_max_seq_length()
        }
