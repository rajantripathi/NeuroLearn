# 🧠 NeuroLearn

**Adaptive AI Study Coach for ADHD University Students**

NeuroLearn is an offline-first MVP that helps learners start tasks, stay focused in short sprints, and manage overwhelm through evidence-based ADHD learning strategies.

⚠️ **Important:** This is a study-support tool, not therapy or medical diagnosis.

---

## 🌟 Features

- **Adaptive Tone**: Dynamically adjusts communication style based on focus state (focused, overwhelmed, distracted)
- **Evidence-Based Strategies**: RAG-powered retrieval of ADHD learning strategies from academic sources
- **Focus Sprints**: Timed focus sessions (5-25 minutes) with progress tracking
- **Document Support**: Upload PDFs/documents for summarization and study help
- **Speech I/O**: Optional voice input (Whisper) and output (pyttsx3)
- **Privacy-First**: All data stored locally in JSON files
- **Offline Capable**: Runs entirely on your machine via Docker

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **LLM**: Ollama - `llama3.1:8b` (~4.9 GB) for chat/coaching
- **Embeddings**: Ollama - `nomic-embed-text:latest` (~274 MB) for RAG
- **Vector Search**: FAISS (lightweight, local)
- **Speech-to-Text**: OpenAI Whisper
- **Text-to-Speech**: pyttsx3
- **Storage**: JSON files (local)
- **Deployment**: Docker Compose

### Model Usage
- **llama3.1:8b**: CHAT ONLY - Never used for embeddings
- **nomic-embed-text:latest**: EMBEDDING ONLY - Never used for chat
- See `MODEL_CONFIG.md` for detailed configuration

---

## 📦 Installation & Setup

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended
- (Optional) NVIDIA GPU for faster LLM inference

### Quick Start

1. **Clone the repository**:
```bash
git clone <repository-url>
cd NeuroLearn
```

2. **Start services with Docker Compose**:
```bash
docker-compose up -d
```

3. **Pull the Ollama models** (first time only - done automatically by start.sh):
```bash
# LLM for chat (4.9 GB)
docker exec -it neurolearn-ollama ollama pull llama3.1:8b

# Embedding model for RAG (274 MB)
docker exec -it neurolearn-ollama ollama pull nomic-embed-text:latest
```

4. **Access the app**:
Open your browser to: `http://localhost:8501`

### Local Development (without Docker)

1. **Install dependencies**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Install and run Ollama separately**:
```bash
# Install from https://ollama.ai
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest
ollama serve
```

3. **Run the app**:
```bash
cd src
streamlit run ui_app.py
```

---

## 📁 Project Structure

```
neurolearn/
├── data/
│   ├── strategies/          # ADHD strategy JSONs (knowledge base)
│   ├── embeddings/          # Cached vector embeddings
│   └── user_sessions/       # User session data (JSON)
├── src/
│   ├── ui_app.py           # Streamlit UI
│   ├── config.py           # Configuration & constants
│   ├── state_manager.py    # Session persistence
│   ├── kb_loader.py        # Knowledge base loader
│   ├── rag_engine.py       # RAG retrieval
│   ├── llm_orchestrator.py # LLM interaction
│   ├── focus_sprint.py     # Timer functionality
│   ├── doc_handler.py      # Document processing
│   └── speech_io.py        # STT/TTS
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🧠 Knowledge Base

The system includes 6 evidence-based ADHD learning strategy files:

1. **Task Initiation** - Overcoming executive function paralysis
2. **Focus Management** - Timed sprints and attention techniques
3. **Emotion Regulation** - Grounding and stress management
4. **Environment Context** - Adapting to study locations
5. **Academic Support** - Reading, writing, and report scaffolds
6. **Reflection** - Metacognitive awareness

**Sources**: Barkley (2015), DuPaul & Weyandt (2006), Brown (2013), Open University, WHO, UNESCO

---

## 🚀 Usage Guide

### 1. Set Your Focus State

Use the sidebar to select how you're feeling:
- **Focused**: Concise, task-oriented guidance
- **Overwhelmed**: Calm, gentle, step-by-step
- **Distracted**: Brief refocus prompts
- **Neutral**: Warm, encouraging tone

### 2. Start a Focus Sprint

- Enter what you'll work on
- Choose duration (5-25 minutes)
- Click "Start Sprint"
- Complete and rate your session

### 3. Chat for Support

Ask questions like:
- "I'm stuck starting my essay, help!"
- "How can I focus better in a noisy café?"
- "I feel overwhelmed by this reading"

### 4. Upload Documents

- Upload PDFs/documents
- Get ADHD-friendly summaries
- Break down complex readings

### 5. Reflect

- Rate your focus after sessions
- Note what helped
- System learns your preferences

---

## 🔒 Privacy & Ethics

- **No cloud logging**: All data stays on your machine
- **Local storage**: JSON files in `data/user_sessions/`
- **No diagnosis**: Politely rejects medical/diagnostic queries
- **Transparent sources**: Cites evidence-based strategies

---

## ⚙️ Configuration

Edit `src/config.py` to customize:

```python
# Model Configuration
LLM_MODEL_NAME = "llama3.1:8b"  # Chat model
EMBED_MODEL_NAME = "nomic-embed-text:latest"  # Embedding model

# Sprint Settings
DEFAULT_SPRINT_DURATION = 10  # minutes

# RAG Settings
MAX_STRATEGY_RESULTS = 3  # Number of strategies to retrieve (2-3 recommended)
```

**Important**: See `MODEL_CONFIG.md` for model usage rules and validation.

---

## 🐛 Troubleshooting

### "Cannot connect to Ollama"
- Ensure Ollama service is running: `docker ps`
- Check logs: `docker logs neurolearn-ollama`

### Slow response times
- Use a smaller model: `ollama pull llama3.2:1b`
- Reduce `max_tokens` in `config.py`

### Speech features not working
- Check microphone permissions
- Whisper models download on first use (may be slow)

---

## 🤝 Contributing

This is an MVP. Potential enhancements:

- [ ] Multi-user support
- [ ] Mobile-friendly UI
- [ ] Calendar integration
- [ ] More KB strategies
- [ ] Analytics dashboard

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

Built with evidence-based ADHD research from:
- Russell Barkley
- Thomas Brown
- Open University
- CHADD & ADDitude Magazine
- WHO & UNESCO Accessibility Guidelines

---

**Built for learners, by understanding.**

For support or questions, please open an issue on GitHub.

