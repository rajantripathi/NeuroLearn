"""
NeuroLearn Configuration Module
Centralizes all paths, settings, and constants.
"""

import os
from pathlib import Path

# Legacy path aliases (for backward compatibility)
STRATEGIES_DIR = None  # Will be set after BASE_DIR
EMBEDDINGS_DIR = None
SESSIONS_DIR = None

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model Assignments
# LLM for adaptive coaching dialogue (chat only - never for embeddings)
LLM_MODEL_NAME = "llama3.1:8b"

# Embedding model for RAG similarity search (embedding only - never for chat)
EMBED_MODEL_NAME = "nomic-embed-text:latest"

# Legacy compatibility
LLM_MODEL = LLM_MODEL_NAME
EMBEDDING_MODEL = EMBED_MODEL_NAME

# Data Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SESSION_STORE_DIR = DATA_DIR / "user_sessions"
STRATEGY_DIR = DATA_DIR / "strategies"
UPLOAD_DIR = DATA_DIR / "uploads"
EMBED_INDEX_DIR = DATA_DIR / "embeddings"

# Ensure directories exist
SESSION_STORE_DIR.mkdir(parents=True, exist_ok=True)
STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EMBED_INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Focus State Definitions
FOCUS_STATES = ["focused", "distracted", "overwhelmed", "neutral"]
DEFAULT_STUDY_ENV = "home"

# Intent Categories
INTENT_CATEGORIES = [
    "task_support",
    "planning",
    "motivation",
    "summarize_document",
    "reflection",
    "general"
]

# Study Environments
STUDY_ENVIRONMENTS = ["home", "library", "cafe", "other"]

# Sprint Settings
DEFAULT_SPRINT_DURATION = 10  # minutes
MIN_SPRINT_DURATION = 5
MAX_SPRINT_DURATION = 25

# RAG Settings
MAX_STRATEGY_RESULTS = 3  # Number of strategy chunks to retrieve
TOP_K_RETRIEVAL = MAX_STRATEGY_RESULTS  # Legacy alias
SIMILARITY_THRESHOLD = 0.5  # Minimum similarity score for retrieval

# Set legacy aliases after directory definitions
STRATEGIES_DIR = STRATEGY_DIR
EMBEDDINGS_DIR = EMBED_INDEX_DIR
SESSIONS_DIR = SESSION_STORE_DIR

# Session Settings
DEFAULT_SESSION_FILENAME = "current_session.json"
SESSION_TIMEOUT_HOURS = 24

# LLM Prompt Templates
SYSTEM_PROMPT_BASE = """You are NeuroLearn, an adaptive AI study coach for university students with ADHD.

Your role:
- Help learners start tasks, stay focused, and manage overwhelm
- Provide evidence-based ADHD learning strategies
- Adapt your tone based on the user's focus state
- Keep responses concise and actionable

Important guidelines:
- This is a study-support tool, NOT medical advice or therapy
- Never diagnose or claim to treat ADHD
- If asked about diagnosis/medication, politely redirect to healthcare professionals
- Always cite sources briefly when using strategies

Tone adaptation:
- focused → concise, task-oriented
- overwhelmed → calm, gentle, one-step-at-a-time
- distracted → supportive refocus, brief
- neutral → warm, encouraging
"""

FALLBACK_RESPONSE = "Let's slow down and try one tiny step together."

DIAGNOSTIC_REJECTION = (
    "I'm here to support your study planning and focus, but I can't provide "
    "medical advice or diagnosis. Please consult a healthcare professional "
    "for questions about ADHD diagnosis or treatment."
)

# UI Settings
APP_TITLE = "🧠 NeuroLearn"
APP_SUBTITLE = "Your Adaptive Study Coach"
DISCLAIMER = "NeuroLearn supports study planning and focus; not medical advice."

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

