#!/bin/bash
echo "🧪 Running NeuroLearn Configuration Validation"
echo ""
echo "Note: Running from host, using http://localhost:11434"
echo "      (Inside Docker, the app uses http://ollama:11434)"
echo ""
python validate_config.py
