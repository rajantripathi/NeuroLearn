# NeuroLearn Setup Guide

## Quick Start

### Using Docker (Recommended)

1. **Start NeuroLearn**:
```bash
./start.sh
```

This script will:
- Start Docker containers
- Download required AI models
- Launch the application

2. **Access the app**: Open `http://localhost:8501` in your browser

3. **Stop when done**:
```bash
docker-compose down
```

---

## Manual Setup

### Step 1: Install Dependencies

**With Docker:**
```bash
docker-compose build
```

**Without Docker (Local Python):**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Install Ollama

**Docker users**: Already included in docker-compose.yml

**Local users**:
1. Download from https://ollama.ai
2. Install and run: `ollama serve`
3. Pull models:
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Step 3: Run the Application

**With Docker:**
```bash
docker-compose up
```

**Without Docker:**
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run NeuroLearn
cd src
streamlit run ui_app.py
```

---

## Configuration

### Change LLM Model

Edit `src/config.py`:
```python
LLM_MODEL = "llama3.2:3b"  # Options: llama2, mistral, phi, etc.
```

Then pull the model:
```bash
docker exec neurolearn-ollama ollama pull <model-name>
# OR locally: ollama pull <model-name>
```

### Adjust Sprint Defaults

Edit `src/config.py`:
```python
DEFAULT_SPRINT_DURATION = 10  # minutes
MIN_SPRINT_DURATION = 5
MAX_SPRINT_DURATION = 25
```

### Enable GPU (NVIDIA)

Docker Compose already includes GPU support. Ensure:
1. NVIDIA drivers installed
2. NVIDIA Container Toolkit installed
3. Uncomment GPU section in `docker-compose.yml` if needed

For CPU-only, remove the `deploy` section in `docker-compose.yml`.

---

## Testing the Installation

1. **Check services are running**:
```bash
docker ps
```
You should see:
- `neurolearn-ollama`
- `neurolearn-app`

2. **Test Ollama**:
```bash
curl http://localhost:11434/api/tags
```

3. **Open the UI**:
Navigate to `http://localhost:8501`

4. **Try a chat message**:
Type: "Help me start my homework"

---

## Troubleshooting

### Port Already in Use

**Ollama (11434)**:
```bash
# Change in docker-compose.yml
ports:
  - "11435:11434"  # Use different external port
```

**Streamlit (8501)**:
```bash
# Change in docker-compose.yml
ports:
  - "8502:8501"  # Use different external port
```

### Models Not Downloading

```bash
# Manually pull models
docker exec -it neurolearn-ollama ollama pull llama3.2:3b
docker exec -it neurolearn-ollama ollama pull nomic-embed-text
```

### Slow Performance

1. Use smaller model:
```bash
ollama pull llama3.2:1b
```

2. Reduce tokens in `src/config.py`:
```python
# In llm_orchestrator.py, reduce max_tokens parameter
```

### Permission Errors (Linux)

```bash
sudo chown -R $USER:$USER data/
```

---

## Data Management

### User Sessions

Stored in: `data/user_sessions/`

Format: JSON files per user

### Knowledge Base

Located in: `data/strategies/`

To add strategies:
1. Create JSON file in format of existing files
2. Restart app or delete `data/embeddings/kb_embeddings.pkl`

### Embeddings Cache

Located in: `data/embeddings/`

To rebuild:
```bash
rm -rf data/embeddings/*
# Restart app - will rebuild automatically
```

---

## Updating

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Uninstalling

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes user data!)
docker-compose down -v

# Remove images
docker rmi neurolearn-app
docker rmi ollama/ollama
```

---

## Getting Help

- Check logs: `docker-compose logs -f`
- Ollama logs: `docker logs neurolearn-ollama`
- App logs: `docker logs neurolearn-app`

For issues, check the main README.md troubleshooting section.

