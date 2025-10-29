"""
LLM Orchestrator Module
Manages interaction with Ollama LLM, prompt building, and response generation.

MODEL USAGE: llama3.1:8b via Ollama
- Purpose: CHAT ONLY (adaptive coaching dialogue)
- Never use this model for embeddings
- Builds prompts with: focus state + study env + retrieved strategies + task context
- Enforces tone templates (calm for overwhelmed, direct for focused, gentle refocus for distracted)
- Appends explainability note: "(Based on ADHD study strategies.)"
"""

import logging
import re
from typing import Dict, Any, List, Optional

import requests

from config import (
    OLLAMA_HOST, LLM_MODEL_NAME, SYSTEM_PROMPT_BASE,
    FALLBACK_RESPONSE, DIAGNOSTIC_REJECTION, MAX_STRATEGY_RESULTS
)
from rag_engine import RAGEngine
from state_manager import StateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Orchestrates LLM interactions with context and safety filters."""
    
    def __init__(self, rag_engine: RAGEngine, state_manager: StateManager):
        """
        Initialize LLM orchestrator.
        
        Args:
            rag_engine: RAG engine for strategy retrieval
            state_manager: State manager for user context
        """
        self.rag_engine = rag_engine
        self.state_manager = state_manager
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
        self.llm_model = LLM_MODEL_NAME
        
        # Diagnostic keywords to filter
        self.diagnostic_keywords = [
            "diagnose", "diagnosis", "do i have adhd", "am i adhd",
            "test for adhd", "adhd test", "medication", "prescribe"
        ]
        
        logger.info(f"LLM Orchestrator using model: {self.llm_model} (chat only)")
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False
    
    def _is_diagnostic_query(self, query: str) -> bool:
        """
        Check if query is asking for medical diagnosis.
        
        Args:
            query: User input
            
        Returns:
            True if diagnostic query detected
        """
        query_lower = query.lower()
        for keyword in self.diagnostic_keywords:
            if keyword in query_lower:
                return True
        return False
    
    def _detect_intent(self, query: str) -> str:
        """
        Simple intent detection based on keywords.
        
        Args:
            query: User input
            
        Returns:
            Detected intent category
        """
        query_lower = query.lower()
        
        # Intent patterns
        if any(word in query_lower for word in ["start", "begin", "stuck", "freeze", "overwhelm"]):
            return "task_support"
        
        if any(word in query_lower for word in ["plan", "schedule", "organize"]):
            return "planning"
        
        if any(word in query_lower for word in ["motivate", "anxious", "stressed", "frustrated"]):
            return "motivation"
        
        if any(word in query_lower for word in ["summarize", "read", "understand", "report", "essay"]):
            return "summarize_document"
        
        if any(word in query_lower for word in ["reflect", "how did", "what worked", "rating"]):
            return "reflection"
        
        if any(word in query_lower for word in ["focus", "distract", "concentrate"]):
            return "planning"
        
        return "general"
    
    def _adapt_tone_for_focus_state(self, focus_state: str) -> str:
        """
        Get tone guidance based on focus state.
        
        Args:
            focus_state: Current focus state
            
        Returns:
            Tone instruction for LLM
        """
        tone_map = {
            "focused": "Be concise and task-oriented. The user is in a good flow state.",
            "overwhelmed": "Be extra calm and gentle. Break everything into tiny, manageable steps. Use simple language.",
            "distracted": "Be brief and supportive. Help refocus with one clear next action.",
            "neutral": "Be warm and encouraging. Maintain a supportive, friendly tone."
        }
        
        return tone_map.get(focus_state, tone_map["neutral"])
    
    def build_prompt(
        self,
        user_query: str,
        retrieved_strategies: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build complete prompt with system instructions, context, and strategies.
        
        Args:
            user_query: User's current input
            retrieved_strategies: Strategies from RAG
            conversation_history: Recent conversation turns
            
        Returns:
            Complete prompt string
        """
        state_summary = self.state_manager.get_state_summary()
        focus_state = state_summary.get("focus_state", "neutral")
        
        # Start with system prompt
        prompt_parts = [SYSTEM_PROMPT_BASE]
        
        # Add tone adaptation
        tone_instruction = self._adapt_tone_for_focus_state(focus_state)
        prompt_parts.append(f"\nCurrent tone guidance: {tone_instruction}\n")
        
        # Add user context
        context_section = f"""
Current User Context:
- Focus state: {focus_state}
- Study environment: {state_summary.get('environment', 'unknown')}
- Completed sprints: {state_summary.get('successful_sprints', 0)}/{state_summary.get('sprint_count', 0)}
- Total focus time: {state_summary.get('total_focus_time', 0)} minutes
"""
        
        if state_summary.get('recent_successful_strategies'):
            context_section += f"- Previously successful: {', '.join(state_summary['recent_successful_strategies'])}\n"
        
        prompt_parts.append(context_section)
        
        # Add retrieved strategies
        if retrieved_strategies:
            strategies_formatted = self.rag_engine.format_retrieved_strategies(retrieved_strategies)
            prompt_parts.append(f"\nRelevant Evidence-Based Strategies:\n{strategies_formatted}\n")
        
        # Add conversation history (last 3 turns)
        if conversation_history:
            recent_history = conversation_history[-3:]
            history_text = "\nRecent conversation:\n"
            for turn in recent_history:
                history_text += f"User: {turn.get('user', '')}\n"
                history_text += f"Assistant: {turn.get('bot', '')}\n"
            prompt_parts.append(history_text)
        
        # Add current query
        prompt_parts.append(f"\nUser's current message: {user_query}\n")
        prompt_parts.append(
            "\nProvide a helpful, evidence-based response. "
            "Keep it concise (2-4 sentences max unless detailed steps needed). "
            "Always end your response with: (Based on ADHD study strategies.)"
        )
        
        full_prompt = "\n".join(prompt_parts)
        return full_prompt
    
    def generate_response(
        self,
        user_query: str,
        max_tokens: int = 300,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate response using Ollama LLM with RAG and safety filters.
        
        Args:
            user_query: User's input
            max_tokens: Maximum response length
            temperature: Sampling temperature
            
        Returns:
            Dictionary with response and metadata
        """
        # Safety check: diagnostic queries
        if self._is_diagnostic_query(user_query):
            logger.warning("Diagnostic query detected")
            return {
                "response": DIAGNOSTIC_REJECTION,
                "intent": "diagnostic_rejected",
                "strategies_used": [],
                "source": "safety_filter"
            }
        
        # Check Ollama connection
        if not self._check_ollama_connection():
            logger.error("Ollama not available, using fallback")
            return {
                "response": FALLBACK_RESPONSE,
                "intent": "error",
                "strategies_used": [],
                "source": "fallback"
            }
        
        # Detect intent
        intent = self._detect_intent(user_query)
        logger.info(f"Detected intent: {intent}")
        
        # Get user state
        state_summary = self.state_manager.get_state_summary()
        focus_state = state_summary.get("focus_state", "neutral")
        environment = state_summary.get("environment", "home")
        
        # Retrieve relevant strategies (top 2-3 as specified)
        retrieved_strategies = self.rag_engine.retrieve(
            query=user_query,
            focus_state=focus_state,
            intent=intent,
            environment=environment,
            top_k=MAX_STRATEGY_RESULTS
        )
        
        # Log retrieval hits
        if retrieved_strategies:
            logger.info(f"Retrieved {len(retrieved_strategies)} strategies:")
            for strat in retrieved_strategies:
                logger.info(f"  - {strat.get('category')} (score: {strat.get('similarity_score', 0):.3f})")
        else:
            logger.warning("No strategies retrieved for query")
        
        # Build prompt
        conversation_history = self.state_manager.state.get("conversation_history", [])
        prompt = self.build_prompt(user_query, retrieved_strategies, conversation_history)
        
        # Call Ollama
        try:
            logger.info(f"Calling Ollama with model: {self.llm_model}")
            logger.info(f"Tone selected for focus state '{focus_state}': {self._adapt_tone_for_focus_state(focus_state)[:50]}...")
            
            payload = {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", FALLBACK_RESPONSE).strip()
                
                # Ensure explainability note is present
                if "(Based on ADHD study strategies.)" not in llm_response:
                    llm_response += " (Based on ADHD study strategies.)"
                
                # Log to conversation history
                self.state_manager.add_conversation_turn(
                    user_message=user_query,
                    bot_response=llm_response,
                    intent=intent
                )
                
                logger.info(f"Response generated successfully. Length: {len(llm_response)} chars")
                
                return {
                    "response": llm_response,
                    "intent": intent,
                    "strategies_used": [s.get('category') for s in retrieved_strategies],
                    "source": "ollama"
                }
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return {
                    "response": FALLBACK_RESPONSE,
                    "intent": intent,
                    "strategies_used": [],
                    "source": "fallback"
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": FALLBACK_RESPONSE,
                "intent": intent,
                "strategies_used": [],
                "source": "error"
            }
    
    def check_model_availability(self) -> bool:
        """
        Check if the configured LLM model is available in Ollama.
        
        Returns:
            True if model is available
        """
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                available = self.llm_model in model_names
                if not available:
                    logger.warning(f"Model {self.llm_model} not found. Available: {model_names}")
                return available
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

