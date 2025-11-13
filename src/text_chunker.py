"""
Text Chunker Module
Uses LLM to intelligently chunk text into logical parts for better readability.
"""

import logging
from typing import List, Dict, Any
import requests
import re

from config import OLLAMA_HOST, LLM_MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """Intelligently chunks text into logical parts using LLM."""
    
    def __init__(self):
        """Initialize text chunker."""
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
        self.llm_model = LLM_MODEL_NAME
        logger.info("Text Chunker initialized")
    
    def _markdown_bold_to_html(self, text: str) -> str:
        """
        Convert markdown bold syntax (**text**) to HTML bold tags.
        
        Args:
            text: Text with markdown bold syntax
            
        Returns:
            Text with HTML bold tags
        """
        # Replace **text** with <strong>text</strong>
        return re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
    
    def chunk_text_with_llm(self, text: str, focus_state: str = "neutral") -> List[Dict[str, Any]]:
        """
        Use LLM to chunk text into logical parts based on semantic meaning.
        
        Args:
            text: The text to chunk
            focus_state: User's current focus state (affects chunking strategy)
            
        Returns:
            List of dictionaries with 'content', 'title', and 'type' for each chunk
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Adjust chunking strategy based on focus state
        chunking_strategy = self._get_chunking_strategy(focus_state)
        
        # Build prompt for LLM
        prompt = f"""You are an AI assistant helping students with ADHD and learning challenges. Your task is to break down the following text into logical, manageable chunks.

Chunking Strategy: {chunking_strategy}

Guidelines:
1. Break the text into logical sections based on topics, concepts, or narrative flow
2. Each chunk should be a complete thought or concept
3. Provide a brief, descriptive title for each chunk (3-7 words)
4. Label each chunk type as: "introduction", "main_point", "example", "conclusion", or "transition"
5. Keep chunks focused and digestible
6. **IMPORTANT FORMATTING**: Bold these specific types of information using **double asterisks**:
   - Dates and years (e.g., **1776**, **January 1, 2020**, **20th century**)
   - Country names (e.g., **France**, **United States**, **China**)
   - People's names (e.g., **Albert Einstein**, **Marie Curie**)
   - Technical terms, names and concepts (e.g., **photosynthesis**, **mitochondria**, **Red Army**)
   - Specific numbers and statistics (e.g., **42%**, **1.5 million**)
   - Important vocabulary words being defined or introduced


Text to chunk:
---
{text[:3000]}
---

Please respond in the following format EXACTLY:
CHUNK 1
Title: [your title here]
Type: [chunk type]
Content: [the actual text content with **dates**, **country names**, **people**, **terms**, and **numbers** bolded]

CHUNK 2
Title: [your title here]
Type: [chunk type]
Content: [the actual text content with **dates**, **country names**, **people**, **terms**, and **numbers** bolded]

...and so on for all logical chunks you identify.

Example of proper bolding: "In **1776**, the **United States** declared independence. **George Washington** led the army and established **democracy** as a governing principle."
"""
        
        try:
            logger.info(f"Chunking text with LLM (focus_state: {focus_state})")
            
            payload = {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent chunking
                    "num_predict": 1500
                }
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "").strip()
                
                # Parse the LLM response into structured chunks
                chunks = self._parse_llm_chunks(llm_response)
                
                if chunks:
                    logger.info(f"Successfully created {len(chunks)} logical chunks")
                    return chunks
                else:
                    logger.warning("LLM didn't return valid chunks, falling back to simple chunking")
                    return self._fallback_chunking(text, focus_state)
            else:
                logger.error(f"LLM error: {response.status_code}")
                return self._fallback_chunking(text, focus_state)
                
        except Exception as e:
            logger.error(f"Error chunking text with LLM: {e}")
            return self._fallback_chunking(text, focus_state)
    
    def _get_chunking_strategy(self, focus_state: str) -> str:
        """
        Get chunking strategy description based on focus state.
        
        Args:
            focus_state: Current user focus state
            
        Returns:
            Description of chunking strategy
        """
        strategies = {
            "focused": "Create moderate-sized chunks (200-300 words) with clear topic divisions.",
            "overwhelmed": "Create very small chunks (100-150 words) focusing on one simple concept at a time. Be extra gentle with information density.",
            "distracted": "Create short, punchy chunks (150-200 words) that can be quickly processed. Each chunk should have a clear single focus.",
            "neutral": "Create balanced chunks (200-250 words) that group related ideas together logically."
        }
        
        return strategies.get(focus_state, strategies["neutral"])
    
    def _parse_llm_chunks(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured chunks.
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Split by "CHUNK" markers
        parts = llm_response.split("CHUNK ")
        
        for part in parts[1:]:  # Skip first empty part
            try:
                lines = part.strip().split('\n')
                
                # Extract title, type, and content
                title = ""
                chunk_type = "main_point"
                content = ""
                
                content_started = False
                content_lines = []
                
                for line in lines:
                    line = line.strip()
                    
                    if line.startswith("Title:"):
                        title = line.replace("Title:", "").strip()
                    elif line.startswith("Type:"):
                        chunk_type = line.replace("Type:", "").strip().lower()
                    elif line.startswith("Content:"):
                        content_started = True
                        content_part = line.replace("Content:", "").strip()
                        if content_part:
                            content_lines.append(content_part)
                    elif content_started and line:
                        content_lines.append(line)
                
                content = " ".join(content_lines).strip()
                
                if content:  # Only add if we have actual content
                    # Convert markdown bold to HTML
                    content = self._markdown_bold_to_html(content)
                    
                    chunks.append({
                        "title": title or "Section",
                        "type": chunk_type,
                        "content": content
                    })
            except Exception as e:
                logger.warning(f"Error parsing chunk: {e}")
                continue
        
        return chunks
    
    def _fallback_chunking(self, text: str, focus_state: str) -> List[Dict[str, Any]]:
        """
        Simple fallback chunking if LLM fails.
        
        Args:
            text: Text to chunk
            focus_state: Current focus state
            
        Returns:
            List of simple chunks
        """
        # Determine chunk size based on focus state
        chunk_sizes = {
            "focused": 300,
            "overwhelmed": 150,
            "distracted": 200,
            "neutral": 250
        }
        
        chunk_size = chunk_sizes.get(focus_state, 250)
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_num = 1
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "title": f"Section {chunk_num}",
                        "type": "main_point",
                        "content": current_chunk.strip()
                    })
                    chunk_num += 1
                current_chunk = para + "\n\n"
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "title": f"Section {chunk_num}",
                "type": "main_point",
                "content": current_chunk.strip()
            })
        
        logger.info(f"Created {len(chunks)} fallback chunks")
        return chunks

