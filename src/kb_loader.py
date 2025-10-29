"""
Knowledge Base Loader Module
Loads ADHD strategy JSONs, creates embeddings, and manages vector storage.

MODEL USAGE: nomic-embed-text:latest via Ollama
- Purpose: EMBEDDING ONLY (RAG similarity search)
- Never use this model for chat generation
- Embeds ADHD strategy JSONs and uploaded document chunks
"""

import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import requests

from config import (
    STRATEGIES_DIR, EMBEDDINGS_DIR, 
    EMBED_MODEL_NAME, OLLAMA_HOST
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBaseLoader:
    """Loads and embeds ADHD learning strategies from JSON files."""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the knowledge base loader.
        
        Args:
            use_cache: Whether to use cached embeddings if available
        """
        self.strategies_dir = STRATEGIES_DIR
        self.embeddings_dir = EMBEDDINGS_DIR
        self.use_cache = use_cache
        
        self.strategies: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.ollama_embed_url = f"{OLLAMA_HOST}/api/embeddings"
        
        self._cache_file = self.embeddings_dir / "kb_embeddings.pkl"
        self._strategies_cache_file = self.embeddings_dir / "strategies.json"
        
        logger.info(f"Using embedding model: {EMBED_MODEL_NAME} (embedding only)")
    
    def load_strategies(self) -> List[Dict[str, Any]]:
        """
        Load all strategy JSON files from the strategies directory.
        
        Returns:
            List of strategy dictionaries
        """
        strategies = []
        
        if not self.strategies_dir.exists():
            logger.error(f"Strategies directory not found: {self.strategies_dir}")
            return strategies
        
        json_files = sorted(self.strategies_dir.glob("*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in {self.strategies_dir}")
            return strategies
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    strategy = json.load(f)
                    strategy['source_file'] = json_file.name
                    strategies.append(strategy)
                    logger.info(f"Loaded strategy: {strategy.get('category')}")
            except json.JSONDecodeError as e:
                logger.error(f"Error loading {json_file}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(strategies)} strategies from knowledge base")
        self.strategies = strategies
        return strategies
    
    def _create_embedding_via_ollama(self, text: str) -> Optional[np.ndarray]:
        """
        Create embedding using Ollama's nomic-embed-text model.
        
        Args:
            text: Text to embed
            
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
            logger.error(f"Error creating embedding via Ollama: {e}")
            return None
    
    def create_embeddings(self, force_rebuild: bool = False) -> np.ndarray:
        """
        Create embeddings for all loaded strategies.
        
        Args:
            force_rebuild: Force recreation even if cache exists
            
        Returns:
            Numpy array of embeddings
        """
        # Check cache first
        if self.use_cache and not force_rebuild and self._cache_file.exists():
            logger.info("Loading embeddings from cache")
            return self._load_embeddings_from_cache()
        
        if not self.strategies:
            logger.warning("No strategies loaded. Call load_strategies() first.")
            return np.array([])
        
        # Create text representations for embedding
        texts_to_embed = []
        for strategy in self.strategies:
            # Combine multiple fields for richer semantic representation
            text = (
                f"Category: {strategy.get('category', '')}. "
                f"Scenario: {strategy.get('scenario', '')}. "
                f"When to use: {', '.join(strategy.get('when_to_use', []))}. "
                f"Strategy: {strategy.get('script_for_bot', '')}. "
                f"Rationale: {strategy.get('rationale', '')}"
            )
            texts_to_embed.append(text)
        
        logger.info(f"Creating embeddings for {len(texts_to_embed)} strategies via Ollama...")
        
        # Create embeddings using Ollama
        embeddings_list = []
        for i, text in enumerate(texts_to_embed):
            logger.info(f"Embedding strategy {i+1}/{len(texts_to_embed)}")
            embedding = self._create_embedding_via_ollama(text)
            if embedding is not None:
                embeddings_list.append(embedding)
            else:
                logger.error(f"Failed to create embedding for strategy {i}")
                return np.array([])
        
        embeddings = np.array(embeddings_list, dtype=np.float32)
        
        self.embeddings = embeddings
        
        # Cache the embeddings
        if self.use_cache:
            self._save_embeddings_to_cache(embeddings)
        
        logger.info(f"Embeddings created: shape {embeddings.shape}")
        return embeddings
    
    def _save_embeddings_to_cache(self, embeddings: np.ndarray):
        """Save embeddings and strategies to cache files."""
        try:
            # Save embeddings
            with open(self._cache_file, 'wb') as f:
                pickle.dump(embeddings, f)
            
            # Save strategies for reference
            with open(self._strategies_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.strategies, f, indent=2, ensure_ascii=False)
            
            logger.info("Embeddings cached successfully")
        except Exception as e:
            logger.error(f"Error caching embeddings: {e}")
    
    def _load_embeddings_from_cache(self) -> np.ndarray:
        """Load embeddings and strategies from cache."""
        try:
            with open(self._cache_file, 'rb') as f:
                embeddings = pickle.load(f)
            
            with open(self._strategies_cache_file, 'r', encoding='utf-8') as f:
                self.strategies = json.load(f)
            
            self.embeddings = embeddings
            logger.info(f"Loaded {len(self.strategies)} strategies from cache")
            return embeddings
        except Exception as e:
            logger.error(f"Error loading from cache: {e}")
            return np.array([])
    
    def initialize(self, force_rebuild: bool = False) -> bool:
        """
        Full initialization: load strategies and create embeddings.
        
        Args:
            force_rebuild: Force recreation of embeddings
            
        Returns:
            True if successful
        """
        try:
            # Try cache first
            if self.use_cache and not force_rebuild and self._cache_file.exists():
                self._load_embeddings_from_cache()
                return True
            
            # Otherwise load fresh
            self.load_strategies()
            if not self.strategies:
                logger.error("No strategies loaded")
                return False
            
            self.create_embeddings(force_rebuild=force_rebuild)
            return self.embeddings is not None and len(self.embeddings) > 0
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    def get_strategy_by_category(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a strategy by its category name.
        
        Args:
            category: Strategy category
            
        Returns:
            Strategy dictionary or None
        """
        for strategy in self.strategies:
            if strategy.get('category') == category:
                return strategy
        return None
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get all loaded strategies."""
        return self.strategies
    
    def get_embeddings(self) -> Optional[np.ndarray]:
        """Get the embeddings array."""
        return self.embeddings

