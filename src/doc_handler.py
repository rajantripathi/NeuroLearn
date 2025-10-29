"""
Document Handler Module
Processes uploaded PDFs and text files for summarization and simplification.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

import PyPDF2
from docx import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentHandler:
    """Handles document upload, extraction, and processing."""
    
    def __init__(self, max_chars: int = 10000):
        """
        Initialize document handler.
        
        Args:
            max_chars: Maximum characters to extract from document
        """
        self.max_chars = max_chars
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text or None on error
        """
        try:
            text_parts = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                logger.info(f"Extracting text from PDF: {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_parts.append(text)
                    
                    # Stop if we've exceeded max_chars
                    current_length = len("".join(text_parts))
                    if current_length > self.max_chars:
                        logger.info(f"Reached max chars limit at page {page_num + 1}")
                        break
            
            full_text = "\n".join(text_parts)
            
            # Truncate if needed
            if len(full_text) > self.max_chars:
                full_text = full_text[:self.max_chars] + "\n... [truncated]"
            
            logger.info(f"Extracted {len(full_text)} characters from PDF")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return None
    
    def extract_text_from_docx(self, docx_path: str) -> Optional[str]:
        """
        Extract text from DOCX file.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            Extracted text or None on error
        """
        try:
            doc = Document(docx_path)
            text_parts = []
            
            for para in doc.paragraphs:
                text_parts.append(para.text)
                
                # Stop if we've exceeded max_chars
                current_length = len("\n".join(text_parts))
                if current_length > self.max_chars:
                    break
            
            full_text = "\n".join(text_parts)
            
            # Truncate if needed
            if len(full_text) > self.max_chars:
                full_text = full_text[:self.max_chars] + "\n... [truncated]"
            
            logger.info(f"Extracted {len(full_text)} characters from DOCX")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return None
    
    def extract_text_from_txt(self, txt_path: str) -> Optional[str]:
        """
        Extract text from plain text file.
        
        Args:
            txt_path: Path to text file
            
        Returns:
            Extracted text or None on error
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                text = file.read(self.max_chars)
            
            logger.info(f"Extracted {len(text)} characters from TXT")
            return text
            
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return None
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """
        Auto-detect file type and extract text.
        
        Args:
            file_path: Path to document
            
        Returns:
            Extracted text or None
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif extension in ['.txt', '.md']:
            return self.extract_text_from_txt(file_path)
        else:
            logger.error(f"Unsupported file type: {extension}")
            return None
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """
        Split text into overlapping chunks for processing.
        
        Args:
            text: Input text
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def create_summary_prompt(self, text: str, focus_state: str = "neutral") -> str:
        """
        Create a prompt for summarizing/simplifying document text.
        
        Args:
            text: Document text to summarize
            focus_state: User's current focus state
            
        Returns:
            Prompt string for LLM
        """
        base_instruction = (
            "You are helping a university student with ADHD understand academic material. "
            "Please provide a clear, structured summary of the following text.\n\n"
        )
        
        # Adapt based on focus state
        if focus_state == "overwhelmed":
            base_instruction += (
                "Keep it very simple. Use bullet points. "
                "Focus only on the main idea and 2-3 key points.\n\n"
            )
        elif focus_state == "distracted":
            base_instruction += (
                "Make it brief and focused. Use clear headings. "
                "Highlight what's most important.\n\n"
            )
        else:
            base_instruction += (
                "Structure the summary with:\n"
                "1. Main topic/purpose (1 sentence)\n"
                "2. Key points (3-5 bullet points)\n"
                "3. Important details or examples\n\n"
            )
        
        prompt = base_instruction + f"Text to summarize:\n\n{text}"
        return prompt
    
    def extract_key_concepts(self, text: str, num_concepts: int = 5) -> list:
        """
        Extract key concepts/keywords from text (simple frequency-based).
        
        Args:
            text: Input text
            num_concepts: Number of concepts to extract
            
        Returns:
            List of key terms
        """
        # Simple word frequency approach
        # Remove common words
        common_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'it', 'its', 'they', 'them', 'their'
        ])
        
        # Tokenize and count
        words = text.lower().split()
        word_freq = {}
        
        for word in words:
            # Clean word
            word = ''.join(c for c in word if c.isalnum())
            
            # Skip short words and common words
            if len(word) < 4 or word in common_words:
                continue
            
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top concepts
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        key_concepts = [word for word, freq in sorted_words[:num_concepts]]
        
        return key_concepts
    
    def get_document_stats(self, text: str) -> Dict[str, Any]:
        """
        Get basic statistics about the document.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with statistics
        """
        words = text.split()
        sentences = text.split('.')
        paragraphs = text.split('\n\n')
        
        # Estimate reading time (average 200 words per minute)
        reading_time_minutes = len(words) / 200
        
        stats = {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "estimated_reading_time_minutes": round(reading_time_minutes, 1)
        }
        
        return stats

