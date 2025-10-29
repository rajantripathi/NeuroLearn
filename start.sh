#!/bin/bash

# NeuroLearn Startup Script

echo "🧠 NeuroLearn - Starting up..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "📦 Starting Docker services..."
docker-compose up -d

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to initialize..."
sleep 5

# Check if models are installed
echo "🔍 Checking for required models..."

# LLM Model (for chat/coaching)
if ! docker exec neurolearn-ollama ollama list | grep -q "llama3.1:8b"; then
    echo "📥 Downloading llama3.1:8b model (~4.9 GB, this may take a while)..."
    docker exec neurolearn-ollama ollama pull llama3.1:8b
else
    echo "✅ llama3.1:8b already installed"
fi

# Embedding Model (for RAG similarity search)
if ! docker exec neurolearn-ollama ollama list | grep -q "nomic-embed-text:latest"; then
    echo "📥 Downloading nomic-embed-text:latest model (~274 MB)..."
    docker exec neurolearn-ollama ollama pull nomic-embed-text:latest
else
    echo "✅ nomic-embed-text:latest already installed"
fi

echo ""
echo "✅ NeuroLearn is ready!"
echo "🌐 Open your browser to: http://localhost:8501"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"

