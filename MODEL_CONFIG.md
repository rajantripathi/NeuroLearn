# NeuroLearn Model Configuration

## Model Assignments

### Embedding Model: `nomic-embed-text:latest`
- **Size**: ~274 MB
- **Purpose**: EMBEDDING ONLY - RAG similarity search
- **Used in**: 
  - `kb_loader.py` - Embeds ADHD strategy JSONs
  - `rag_engine.py` - Encodes user queries for similarity search
- **Operations**:
  - Embed ADHD strategy JSONs from `data/strategies/`
  - Embed uploaded study text/PDF chunks
  - Compute cosine similarity to retrieve top 2-3 relevant strategy snippets
- **Rule**: NEVER use for chat generation

### LLM Model: `llama3.1:8b`
- **Size**: ~4.9 GB
- **Purpose**: CHAT ONLY - Adaptive coaching dialogue
- **Used in**:
  - `llm_orchestrator.py` - Generates assistant responses
- **Operations**:
  - Build prompts using: focus state + study env + retrieved strategies + task context
  - Enforce tone templates:
    - **overwhelmed** → calm, gentle, step-by-step
    - **focused** → direct, concise, task-oriented
    - **distracted** → gentle refocus, brief
  - Append explainability note: "(Based on ADHD study strategies.)"
- **Rule**: NEVER use for embeddings

---

## Configuration File: `src/config.py`

```python
# Ollama host
OLLAMA_HOST = "http://ollama:11434"

# Models
LLM_MODEL_NAME = "llama3.1:8b"          # Chat only
EMBED_MODEL_NAME = "nomic-embed-text:latest"  # Embedding only

# Data directories
SESSION_STORE_DIR = "data/user_sessions"
STRATEGY_DIR = "data/strategies"
UPLOAD_DIR = "data/uploads"
EMBED_INDEX_DIR = "data/embeddings"

# App constants
MAX_STRATEGY_RESULTS = 3
FOCUS_STATES = ["focused", "distracted", "overwhelmed"]
DEFAULT_STUDY_ENV = "home"
```

---

## Pipeline Flow

1. **User Query** → `llm_orchestrator.py`
   
2. **Embedding Query** → `rag_engine.py` 
   - Uses `nomic-embed-text:latest` via Ollama `/api/embeddings`
   - Creates query vector
   
3. **Retrieve Strategies** → `rag_engine.py`
   - Computes cosine similarity against pre-embedded KB
   - Returns top 2-3 matches (MAX_STRATEGY_RESULTS)
   - Logs retrieval hits with scores
   
4. **Build Prompt** → `llm_orchestrator.py`
   - Includes: system prompt + user context + retrieved strategies + tone guidance
   - Logs tone selection for focus state
   
5. **Generate Response** → `llm_orchestrator.py`
   - Uses `llama3.1:8b` via Ollama `/api/generate`
   - Enforces tone based on focus state
   - Appends: "(Based on ADHD study strategies.)"
   
6. **Return Response** → UI

---

## Optional/Future Models

### deepseek-r1:32b
- **Status**: NOT used by default
- **Purpose**: High-reasoning experiments only
- **Size**: ~20 GB
- **Note**: Only pull if explicitly needed for advanced reasoning tasks

### llama3:latest
- **Status**: Fallback only
- **Note**: Use only if llama3.1:8b fails to load

---

## Validation Logging

Each module logs its model usage:

```
INFO: Using embedding model: nomic-embed-text:latest (embedding only)
INFO: RAG engine using embedding model: nomic-embed-text:latest (embedding only)
INFO: LLM Orchestrator using model: llama3.1:8b (chat only)
INFO: Retrieved 2 strategies:
INFO:   - task_initiation (score: 0.847)
INFO:   - focus_management (score: 0.723)
INFO: Tone selected for focus state 'overwhelmed': Be extra calm and gentle...
INFO: Response generated successfully. Length: 187 chars
```

---

## Testing the Configuration

Run one test conversation and verify logs show:

1. ✅ Correct embedding model used for query encoding
2. ✅ Correct LLM used for response generation
3. ✅ Retrieval hits logged with similarity scores
4. ✅ Tone selection logged based on focus state
5. ✅ Response includes: "(Based on ADHD study strategies.)"

Example test:
```python
user_query = "I'm overwhelmed and can't start my homework"
# Expected:
# - nomic-embed-text encodes query
# - Retrieves task_initiation strategy
# - llama3.1:8b generates calm, step-by-step response
# - Tone: calm, gentle
# - Ends with explainability note
```

---

## Model Pull Commands

```bash
# Pull embedding model
docker exec neurolearn-ollama ollama pull nomic-embed-text:latest

# Pull LLM model
docker exec neurolearn-ollama ollama pull llama3.1:8b

# List installed models
docker exec neurolearn-ollama ollama list
```

---

## Troubleshooting

**"Model not found" error:**
```bash
docker exec neurolearn-ollama ollama pull llama3.1:8b
docker exec neurolearn-ollama ollama pull nomic-embed-text:latest
docker-compose restart
```

**Wrong model being used:**
- Check `src/config.py` settings
- Verify logs show correct model names
- Restart containers after config changes

**Slow embeddings:**
- Embeddings are cached after first run
- Delete `data/embeddings/kb_embeddings.pkl` to rebuild
- Check Ollama logs: `docker logs neurolearn-ollama`

