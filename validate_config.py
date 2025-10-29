#!/usr/bin/env python3
"""
NeuroLearn Configuration Validation Script
Tests that models are correctly configured and pipeline works as expected.
"""

import sys
import logging
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import requests
from config import (
    LLM_MODEL_NAME, EMBED_MODEL_NAME, OLLAMA_HOST,
    MAX_STRATEGY_RESULTS, FOCUS_STATES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-detect if running from host (use localhost) or inside Docker (use ollama)
# When running validate_config.py from host, we need localhost:11434
VALIDATION_OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST", 
    "http://localhost:11434"  # Default to localhost for validation from host
)


def check_ollama_connection():
    """Test connection to Ollama service."""
    logger.info("=" * 60)
    logger.info("VALIDATION: Ollama Connection")
    logger.info("=" * 60)
    
    logger.info(f"Testing connection to: {VALIDATION_OLLAMA_HOST}")
    logger.info(f"(Config default: {OLLAMA_HOST})")
    
    try:
        response = requests.get(f"{VALIDATION_OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Ollama accessible at {VALIDATION_OLLAMA_HOST}")
            
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            logger.info(f"\nInstalled models: {len(models)}")
            for model in models:
                logger.info(f"  - {model.get('name')} ({model.get('size', 'unknown size')})")
            
            return True, model_names
        else:
            logger.error(f"❌ Ollama returned status {response.status_code}")
            return False, []
    except Exception as e:
        logger.error(f"❌ Cannot connect to Ollama: {e}")
        return False, []


def check_model_availability(model_names):
    """Check if required models are installed."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION: Model Availability")
    logger.info("=" * 60)
    
    llm_available = LLM_MODEL_NAME in model_names
    embed_available = EMBED_MODEL_NAME in model_names
    
    logger.info(f"\nLLM Model ({LLM_MODEL_NAME}):")
    if llm_available:
        logger.info(f"  ✅ Installed - Purpose: CHAT ONLY")
    else:
        logger.error(f"  ❌ NOT FOUND - Run: docker exec neurolearn-ollama ollama pull {LLM_MODEL_NAME}")
    
    logger.info(f"\nEmbedding Model ({EMBED_MODEL_NAME}):")
    if embed_available:
        logger.info(f"  ✅ Installed - Purpose: EMBEDDING ONLY")
    else:
        logger.error(f"  ❌ NOT FOUND - Run: docker exec neurolearn-ollama ollama pull {EMBED_MODEL_NAME}")
    
    return llm_available, embed_available


def test_embedding_creation():
    """Test creating embeddings via Ollama."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION: Embedding Creation")
    logger.info("=" * 60)
    
    try:
        test_text = "I'm feeling overwhelmed and can't start my homework"
        
        payload = {
            "model": EMBED_MODEL_NAME,
            "prompt": test_text
        }
        
        response = requests.post(
            f"{VALIDATION_OLLAMA_HOST}/api/embeddings",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            
            logger.info(f"✅ Embedding created successfully")
            logger.info(f"  - Model: {EMBED_MODEL_NAME}")
            logger.info(f"  - Input: '{test_text}'")
            logger.info(f"  - Output dimension: {len(embedding)}")
            logger.info(f"  - Sample values: {embedding[:5]}")
            return True
        else:
            logger.error(f"❌ Embedding failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creating embedding: {e}")
        return False


def test_llm_generation():
    """Test LLM response generation."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION: LLM Response Generation")
    logger.info("=" * 60)
    
    try:
        test_prompt = (
            "You are a helpful ADHD study coach. "
            "Respond to: 'I'm overwhelmed and can't start my homework' "
            "Be calm and gentle. End with: (Based on ADHD study strategies.)"
        )
        
        payload = {
            "model": LLM_MODEL_NAME,
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 150
            }
        }
        
        logger.info(f"Calling LLM model: {LLM_MODEL_NAME}...")
        
        response = requests.post(
            f"{VALIDATION_OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "").strip()
            
            logger.info(f"✅ LLM response generated successfully")
            logger.info(f"  - Model: {LLM_MODEL_NAME}")
            logger.info(f"  - Response length: {len(llm_response)} chars")
            logger.info(f"  - Response preview: {llm_response[:200]}...")
            
            # Check for explainability note
            if "(Based on ADHD study strategies.)" in llm_response:
                logger.info(f"  ✅ Explainability note present")
            else:
                logger.warning(f"  ⚠️ Missing explainability note - will be added automatically")
            
            return True
        else:
            logger.error(f"❌ LLM generation failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error generating LLM response: {e}")
        return False


def check_config_values():
    """Validate configuration values."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION: Configuration Values")
    logger.info("=" * 60)
    
    logger.info(f"\n🔧 Config Settings:")
    logger.info(f"  - Ollama Host (in Docker): {OLLAMA_HOST}")
    logger.info(f"  - Ollama Host (validation): {VALIDATION_OLLAMA_HOST}")
    logger.info(f"  - LLM Model: {LLM_MODEL_NAME} (chat only)")
    logger.info(f"  - Embedding Model: {EMBED_MODEL_NAME} (embedding only)")
    logger.info(f"  - Max Strategy Results: {MAX_STRATEGY_RESULTS}")
    logger.info(f"  - Focus States: {FOCUS_STATES}")
    
    # Check for common mistakes
    issues = []
    
    if "embed" in LLM_MODEL_NAME.lower():
        issues.append("⚠️ LLM model name contains 'embed' - should be chat model")
    
    if "llama" in EMBED_MODEL_NAME.lower() or "gpt" in EMBED_MODEL_NAME.lower():
        issues.append("⚠️ Embedding model looks like a chat model")
    
    if MAX_STRATEGY_RESULTS < 2 or MAX_STRATEGY_RESULTS > 5:
        issues.append(f"⚠️ MAX_STRATEGY_RESULTS={MAX_STRATEGY_RESULTS} is outside recommended range (2-3)")
    
    if issues:
        logger.warning("\n" + "\n".join(issues))
    else:
        logger.info("\n✅ All config values look correct")
    
    return len(issues) == 0


def main():
    """Run all validation checks."""
    logger.info("\n" + "=" * 60)
    logger.info("🧠 NeuroLearn Model Configuration Validation")
    logger.info("=" * 60)
    
    results = {}
    
    # 1. Check Ollama connection
    ollama_ok, model_names = check_ollama_connection()
    results['ollama'] = ollama_ok
    
    if not ollama_ok:
        logger.error("\n❌ Cannot proceed without Ollama connection")
        return False
    
    # 2. Check model availability
    llm_ok, embed_ok = check_model_availability(model_names)
    results['models'] = llm_ok and embed_ok
    
    # 3. Check config values
    config_ok = check_config_values()
    results['config'] = config_ok
    
    # 4. Test embedding (if model available)
    if embed_ok:
        embed_test_ok = test_embedding_creation()
        results['embedding_test'] = embed_test_ok
    else:
        results['embedding_test'] = False
    
    # 5. Test LLM (if model available)
    if llm_ok:
        llm_test_ok = test_llm_generation()
        results['llm_test'] = llm_test_ok
    else:
        results['llm_test'] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All validations passed! NeuroLearn is ready to use.")
        return True
    else:
        logger.error("\n⚠️ Some validations failed. Please fix issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

