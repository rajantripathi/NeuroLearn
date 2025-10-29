"""
RAG (Retrieval-Augmented Generation) Engine
Retrieves relevant ADHD strategies based on user query and context.

MODEL USAGE: nomic-embed-text:latest via Ollama
- Purpose: EMBEDDING ONLY (query encoding for similarity search)
- Never use this model for chat generation
- Computes cosine similarity to retrieve top 2-3 relevant strategy snippets
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import requests

from config import (
    TOP_K_RETRIEVAL, SIMILARITY_THRESHOLD, MAX_STRATEGY_RESULTS,
    EMBED_MODEL_NAME, OLLAMA_HOST
)
from kb_loader import KnowledgeBaseLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval engine for finding relevant ADHD learning strategies."""
    
    def __init__(self, kb_loader: KnowledgeBaseLoader):
        """
        Initialize RAG engine with a knowledge base loader.
        
        Args:
            kb_loader: Initialized KnowledgeBaseLoader instance
        """
        self.kb_loader = kb_loader
        self.ollama_embed_url = f"{OLLAMA_HOST}/api/embeddings"
        
        # Ensure KB is loaded
        if not kb_loader.strategies or kb_loader.embeddings is None:
            logger.info("Initializing knowledge base...")
            kb_loader.initialize()
        
        logger.info(f"RAG engine using embedding model: {EMBED_MODEL_NAME} (embedding only)")
    
    def _create_query_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Create embedding for query using Ollama's nomic-embed-text model.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            payload = {
                "model": EMBED_MODEL_NAME,
                "prompt": text
            }
            
            response = requests.post(
                self.ollama_embed_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                return np.array(embedding, dtype=np.float32)
            else:
                logger.error(f"Ollama embedding error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating query embedding via Ollama: {e}")
            return None
    
    def _compute_similarity(self, query_embedding: np.ndarray, 
                           doc_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and document embeddings.
        
        Args:
            query_embedding: Query vector
            doc_embeddings: Document vectors
            
        Returns:
            Array of similarity scores
        """
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        
        # Cosine similarity
        similarities = np.dot(doc_norms, query_norm)
        return similarities
    
    def retrieve(
        self,
        query: str,
        focus_state: Optional[str] = None,
        intent: Optional[str] = None,
        environment: Optional[str] = None,
        top_k: int = TOP_K_RETRIEVAL
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant strategies based on query and context.
        
        Args:
            query: User's question or input
            focus_state: Current focus state (focused/distracted/overwhelmed)
            intent: Detected intent category
            environment: Study environment
            top_k: Number of results to return
            
        Returns:
            List of relevant strategy dictionaries with similarity scores
        """
        if self.kb_loader.embeddings is None:
            logger.error("Knowledge base not initialized")
            return []
        
        # Enhance query with context
        enhanced_query = self._build_enhanced_query(query, focus_state, intent, environment)
        
        # Create query embedding via Ollama
        logger.info(f"Retrieving strategies for query: {query[:50]}...")
        query_embedding = self._create_query_embedding(enhanced_query)
        
        if query_embedding is None:
            logger.error("Failed to create query embedding")
            return []
        
        # Compute similarities
        similarities = self._compute_similarity(
            query_embedding,
            self.kb_loader.embeddings
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results with metadata
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            
            # Filter by threshold
            if score < SIMILARITY_THRESHOLD:
                continue
            
            strategy = self.kb_loader.strategies[idx].copy()
            strategy['similarity_score'] = score
            results.append(strategy)
        
        logger.info(f"Retrieved {len(results)} relevant strategies")
        return results
    
    def _build_enhanced_query(
        self,
        query: str,
        focus_state: Optional[str],
        intent: Optional[str],
        environment: Optional[str]
    ) -> str:
        """
        Enhance query with contextual information for better retrieval.
        
        Args:
            query: Original query
            focus_state: Focus state
            intent: Intent category
            environment: Study environment
            
        Returns:
            Enhanced query string
        """
        context_parts = [query]
        
        if focus_state:
            context_parts.append(f"User feeling: {focus_state}")
        
        if intent:
            context_parts.append(f"Intent: {intent}")
        
        if environment:
            context_parts.append(f"Environment: {environment}")
        
        enhanced = ". ".join(context_parts)
        return enhanced
    
    def retrieve_by_focus_state(
        self,
        focus_state: str,
        top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieve strategies specifically matching a focus state.
        
        Args:
            focus_state: Target focus state
            top_k: Number of results
            
        Returns:
            List of matching strategies
        """
        matching_strategies = []
        
        for strategy in self.kb_loader.strategies:
            when_to_use = strategy.get('when_to_use', [])
            
            # Check if any condition matches the focus state
            for condition in when_to_use:
                if f"focus_state={focus_state}" in condition or focus_state in condition:
                    matching_strategies.append(strategy)
                    break
        
        logger.info(f"Found {len(matching_strategies)} strategies for focus_state={focus_state}")
        return matching_strategies[:top_k]
    
    def retrieve_by_intent(
        self,
        intent: str,
        top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieve strategies specifically matching an intent.
        
        Args:
            intent: Target intent category
            top_k: Number of results
            
        Returns:
            List of matching strategies
        """
        matching_strategies = []
        
        for strategy in self.kb_loader.strategies:
            when_to_use = strategy.get('when_to_use', [])
            
            # Check conditions and category
            for condition in when_to_use:
                if f"intent={intent}" in condition or intent in condition:
                    matching_strategies.append(strategy)
                    break
            
            # Also check category
            if strategy.get('category') and intent in strategy.get('category', ''):
                if strategy not in matching_strategies:
                    matching_strategies.append(strategy)
        
        logger.info(f"Found {len(matching_strategies)} strategies for intent={intent}")
        return matching_strategies[:top_k]
    
    def format_retrieved_strategies(self, strategies: List[Dict[str, Any]]) -> str:
        """
        Format retrieved strategies for inclusion in LLM prompt.
        
        Args:
            strategies: List of strategy dictionaries
            
        Returns:
            Formatted string for prompt
        """
        if not strategies:
            return "No specific strategies retrieved."
        
        formatted_parts = []
        for i, strategy in enumerate(strategies, 1):
            part = f"\n--- Strategy {i}: {strategy.get('category', 'unknown')} ---\n"
            part += f"Scenario: {strategy.get('scenario', '')}\n"
            part += f"Recommended approach: {strategy.get('script_for_bot', '')}\n"
            part += f"Why this works: {strategy.get('rationale', '')}\n"
            part += f"Source: {strategy.get('source', '')}\n"
            
            formatted_parts.append(part)
        
        result = "\n".join(formatted_parts)
        result += "\n\n(Based on ADHD study strategies.)"
        return result

