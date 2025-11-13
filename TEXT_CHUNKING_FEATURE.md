# 📚 Text Chunking with OpenDyslexic Font

## Overview
NeuroLearn now includes an **AI-powered text chunking feature** that breaks down long texts into logical, manageable parts and displays them using the **OpenDyslexic font** - a typeface designed specifically to improve readability for people with dyslexia.

## Features

### 🤖 LLM-Based Text Chunking
- Uses the LLM to intelligently analyze text and break it into logical sections
- Identifies different types of content: introductions, main points, examples, conclusions, and transitions
- Automatically generates descriptive titles for each chunk
- Adapts chunk size based on your current focus state:
  - **Focused**: Moderate chunks (200-300 words)
  - **Overwhelmed**: Very small chunks (100-150 words) 
  - **Distracted**: Short, punchy chunks (150-200 words)
  - **Neutral**: Balanced chunks (200-250 words)

### 🔤 OpenDyslexic Font Display
- All chunked text is displayed using the OpenDyslexic font family
- Larger font size (1.1rem) with increased line spacing (1.8)
- Better letter spacing for improved readability
- Bold titles for better visual hierarchy
- Color-coded borders by content type:
  - 🟢 Green: Introduction
  - 🔵 Blue: Main Point
  - 🟠 Orange: Example
  - 🟣 Purple: Conclusion
  - ⚫ Gray: Transition

## How to Use

### Method 1: Upload a Document
1. Open NeuroLearn at http://localhost:8501
2. Click on **"📄 Upload Document for Help"** expander
3. Upload a PDF, TXT, or DOCX file
4. Click **"📚 Chunk into Parts"** button
5. Wait for the LLM to analyze and chunk your text
6. Scroll down to see the chunked view with OpenDyslexic font

### Method 2: Paste Text Directly
1. Open NeuroLearn at http://localhost:8501
2. Click on **"✂️ Chunk Text Directly"** expander
3. Paste your text into the text area (minimum 50 characters)
4. Click **"📚 Chunk This Text"** button
5. The LLM will process and display your chunks below

### Clear Chunked View
- Click the **"✖️ Clear Chunked View"** button at the bottom of the chunked display to remove it

## Technical Details

### Font Files
- Location: `/home/aut/NeuroLearn/font/`
- Files:
  - `OpenDyslexic-Regular.ttf` - Regular weight
  - `OpenDyslexic-Bold.ttf` - Bold weight for titles
  - Fonts are embedded as base64 in the CSS for immediate availability

### Modules
- **`src/text_chunker.py`**: Core text chunking logic
  - `chunk_text_with_llm()`: Main LLM-based chunking function
  - `_parse_llm_chunks()`: Parses LLM output into structured chunks
  - `_fallback_chunking()`: Simple chunking if LLM fails
  
- **`src/ui_app.py`**: Updated UI components
  - `load_font_base64()`: Loads OpenDyslexic fonts
  - `render_chunked_text()`: Displays chunks with custom styling
  - `render_text_chunker()`: Direct text input interface

### Chunk Structure
Each chunk contains:
```python
{
    "title": "Brief descriptive title",
    "type": "main_point",  # or: introduction, example, conclusion, transition
    "content": "The actual text content of this logical section..."
}
```

## Benefits for ADHD/Learning Challenges

1. **Reduced Cognitive Load**: Breaking text into smaller parts makes it less overwhelming
2. **Better Focus**: Visual chunking helps maintain attention on one concept at a time
3. **Improved Comprehension**: Logical grouping helps understand relationships between ideas
4. **Enhanced Readability**: OpenDyslexic font reduces reading difficulties
5. **Adaptive Strategy**: Chunk size adapts to your current mental state

## Example Use Cases

- **Reading Academic Papers**: Break down dense research papers into digestible sections
- **Study Notes**: Organize long lecture notes into logical topics
- **Essay Reading**: Understand structure by seeing introduction, body, and conclusion separately
- **Article Comprehension**: Parse news articles or blog posts into main ideas
- **Textbook Chapters**: Break down lengthy textbook sections into manageable parts

## Troubleshooting

**Issue**: Chunking takes a long time
- **Solution**: This is normal for the first chunk as the LLM analyzes the text structure. Subsequent chunks are faster.

**Issue**: Font doesn't appear
- **Solution**: Ensure font files exist in `/home/aut/NeuroLearn/font/`. The app will fall back to system fonts if OpenDyslexic isn't available.

**Issue**: Chunks aren't logical
- **Solution**: Try adjusting your focus state in the sidebar. Different states may produce different chunking strategies.

**Issue**: LLM chunking fails
- **Solution**: The system automatically falls back to simple paragraph-based chunking if the LLM is unavailable.

## Future Enhancements

Potential improvements planned:
- [ ] Adjustable font size preference
- [ ] More OpenDyslexic font weights (Italic, Bold-Italic)
- [ ] Export chunked text to PDF
- [ ] Save and resume reading progress
- [ ] Audio playback of chunks with TTS
- [ ] Highlighting and annotation features

## Credits

- **OpenDyslexic Font**: Created by Abelardo Gonzalez (https://opendyslexic.org/)
- **License**: SIL Open Font License 1.1

