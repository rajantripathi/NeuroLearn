# NeuroLearn Quick Reference Card

## 🎯 Model Configuration

| Aspect | Embedding Model | LLM Model |
|--------|----------------|-----------|
| **Name** | `nomic-embed-text:latest` | `llama3.1:8b` |
| **Size** | ~274 MB | ~4.9 GB |
| **Purpose** | Embedding ONLY | Chat ONLY |
| **Used In** | `kb_loader.py`, `rag_engine.py` | `llm_orchestrator.py` |
| **API Endpoint** | `/api/embeddings` | `/api/generate` |
| **DO Use For** | • Strategy embeddings<br>• Query encoding<br>• Document chunks<br>• Similarity search | • Coaching responses<br>• Adaptive dialogue<br>• Tone adjustment<br>• Task support |
| **NEVER Use For** | ❌ Chat generation | ❌ Embeddings |

---

## 📝 Configuration File (`src/config.py`)

```python
# Ollama
OLLAMA_HOST = "http://ollama:11434"

# Models (DO NOT MIX!)
LLM_MODEL_NAME = "llama3.1:8b"          # Chat only
EMBED_MODEL_NAME = "nomic-embed-text:latest"  # Embedding only

# Directories
SESSION_STORE_DIR = "data/user_sessions"
STRATEGY_DIR = "data/strategies"
UPLOAD_DIR = "data/uploads"
EMBED_INDEX_DIR = "data/embeddings"

# Constants
MAX_STRATEGY_RESULTS = 3  # Retrieves top 2-3 strategies
FOCUS_STATES = ["focused", "distracted", "overwhelmed"]
DEFAULT_STUDY_ENV = "home"
```

---

## 🔄 Pipeline Flow

```
User Query
    ↓
[Intent Detection] (llm_orchestrator.py)
    ↓
[Embed Query] → nomic-embed-text:latest → Query Vector
    ↓
[Similarity Search] → Cosine similarity vs KB embeddings
    ↓
[Retrieve Strategies] → Top 2-3 matches (MAX_STRATEGY_RESULTS)
    ↓
[Build Prompt] → System + Context + Strategies + Tone
    ↓
[Generate Response] → llama3.1:8b → Adaptive response
    ↓
[Append Note] → "(Based on ADHD study strategies.)"
    ↓
Return to User
```

---

## 🚀 Common Commands

### Start NeuroLearn
```bash
./start.sh
```

### Pull Models Manually
```bash
docker exec neurolearn-ollama ollama pull llama3.1:8b
docker exec neurolearn-ollama ollama pull nomic-embed-text:latest
```

### Validate Configuration
```bash
# Run from host (auto-uses localhost:11434)
python validate_config.py

# Or specify Ollama host explicitly
OLLAMA_HOST=http://localhost:11434 python validate_config.py
```

### Check Logs
```bash
docker logs neurolearn-ollama      # Ollama logs
docker logs neurolearn-app          # App logs
docker-compose logs -f              # Follow all logs
```

### Rebuild Embeddings
```bash
rm -rf data/embeddings/kb_embeddings.pkl
docker-compose restart
```

---

## 🧪 Test Queries

| Focus State | Sample Query | Expected Tone |
|-------------|-------------|---------------|
| **overwhelmed** | "I can't start my homework" | Calm, gentle, step-by-step |
| **distracted** | "I keep losing focus" | Brief, gentle refocus |
| **focused** | "What's next on my list?" | Concise, task-oriented |

**All responses must end with:** `(Based on ADHD study strategies.)`

---

## 📊 Validation Checks

```bash
python validate_config.py
```

Verifies:
- ✅ Ollama connection (`http://ollama:11434`)
- ✅ Models installed (`llama3.1:8b`, `nomic-embed-text:latest`)
- ✅ Config values correct
- ✅ Embedding creation works
- ✅ LLM generation works

---

## 🔍 Key Log Messages

### ✅ Success Indicators
```
INFO: Using embedding model: nomic-embed-text:latest (embedding only)
INFO: LLM Orchestrator using model: llama3.1:8b (chat only)
INFO: Retrieved 2 strategies:
INFO:   - task_initiation (score: 0.847)
INFO: Response generated successfully. Length: 187 chars
```

### ⚠️ Warning Signs
```
WARNING: Model llama3.1:8b not found
ERROR: Cannot connect to Ollama
ERROR: Failed to create query embedding
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Model not found" | `docker exec neurolearn-ollama ollama pull <model>` |
| "Cannot connect to Ollama" | Check `docker ps`, restart: `docker-compose restart` |
| Slow embeddings | Normal on first run, cached after. Delete cache to rebuild. |
| Wrong tone | Check focus state in sidebar, verify logs show correct state |
| No strategies retrieved | Check `data/strategies/` has JSONs, rebuild embeddings |

---

## 📁 File Locations

| What | Where |
|------|-------|
| Config | `src/config.py` |
| Knowledge Base | `data/strategies/*.json` (6 files) |
| Embeddings Cache | `data/embeddings/kb_embeddings.pkl` |
| User Sessions | `data/user_sessions/*.json` |
| Uploads | `data/uploads/` |
| Logs | `docker logs neurolearn-app` |

---

## ⚡ Quick Fixes

**Reset Everything:**
```bash
docker-compose down
rm -rf data/embeddings/*
./start.sh
```

**Force Model Re-download:**
```bash
docker exec neurolearn-ollama ollama rm llama3.1:8b
docker exec neurolearn-ollama ollama pull llama3.1:8b
```

**Check Model List:**
```bash
docker exec neurolearn-ollama ollama list
```

---

## 🎯 Remember

1. **nomic-embed-text:latest** = Embedding ONLY
2. **llama3.1:8b** = Chat ONLY
3. Top 2-3 strategies retrieved per query
4. All responses end with explainability note
5. Tone adapts to focus state
6. Everything stored locally (privacy-first)

---

**For detailed info, see:**
- `MODEL_CONFIG.md` - Complete model guide
- `MODEL_UPDATE_SUMMARY.md` - Change log
- `README.md` - Full documentation

