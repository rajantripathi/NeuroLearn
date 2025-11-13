"""
NeuroLearn Streamlit UI
Main user interface for the adaptive study coach.
"""

import streamlit as st
import streamlit.components.v1 as components
import time
import base64
import html
import re
from datetime import datetime
from pathlib import Path

from config import (
    APP_TITLE, APP_SUBTITLE, DISCLAIMER,
    FOCUS_STATES, STUDY_ENVIRONMENTS
)
from state_manager import StateManager
from kb_loader import KnowledgeBaseLoader
from rag_engine import RAGEngine
from llm_orchestrator import LLMOrchestrator
from focus_sprint import FocusSprint
from doc_handler import DocumentHandler
from text_chunker import TextChunker


def get_audio_base64(audio_path: Path) -> str:
    """
    Convert audio file to base64 string for embedding in HTML.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Base64 encoded string
    """
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        return base64.b64encode(audio_bytes).decode()


# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load OpenDyslexic font
def load_font_base64():
    """Load OpenDyslexic fonts as base64."""
    fonts = {}
    try:
        font_dir = Path(__file__).parent.parent / "font"
        
        regular_path = font_dir / "OpenDyslexic-Regular.ttf"
        if regular_path.exists():
            with open(regular_path, 'rb') as f:
                fonts['regular'] = base64.b64encode(f.read()).decode()
        
        bold_path = font_dir / "OpenDyslexic-Bold.ttf"
        if bold_path.exists():
            with open(bold_path, 'rb') as f:
                fonts['bold'] = base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Warning: Could not load OpenDyslexic fonts: {e}")
    
    return fonts

def render_css():
    """Render CSS styles (only once per session)."""
    if 'css_rendered' not in st.session_state:
        fonts_base64 = load_font_base64()
        
        font_face_css = ""
        if fonts_base64.get('regular'):
            font_face_css += f"""
            @font-face {{
                font-family: 'OpenDyslexic';
                src: url(data:font/truetype;charset=utf-8;base64,{fonts_base64['regular']}) format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            """
        
        if fonts_base64.get('bold'):
            font_face_css += f"""
            @font-face {{
                font-family: 'OpenDyslexic';
                src: url(data:font/truetype;charset=utf-8;base64,{fonts_base64['bold']}) format('truetype');
                font-weight: bold;
                font-style: normal;
            }}
            """
        
        st.markdown(f"""
        <style>
            {font_face_css}
            
            /* Hide Streamlit default elements in focus mode */
            .focus-mode header,
            .focus-mode footer,
            .focus-mode [data-testid="stSidebar"],
            .focus-mode [data-testid="stToolbar"],
            .focus-mode [data-testid="stDecoration"],
            .focus-mode [data-testid="stStatusWidget"] {{
                display: none !important;
            }}
            
            .focus-mode .main {{
                padding: 0 !important;
                max-width: 100% !important;
            }}
            
            .focus-mode .block-container {{
                padding: 0 !important;
                max-width: 100% !important;
            }}
            
            .welcome-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 80vh;
                text-align: center;
                padding: 2rem;
            }}
            
            .welcome-title {{
                font-size: 3rem;
                font-weight: bold;
                color: #4A90E2;
                margin-bottom: 1rem;
                font-family: 'OpenDyslexic', Arial, sans-serif;
            }}
            
            .welcome-subtitle {{
                font-size: 1.5rem;
                color: #666;
                margin-bottom: 3rem;
                font-family: 'OpenDyslexic', Arial, sans-serif;
            }}
            
            .upload-area {{
                border: 3px dashed #4A90E2;
                border-radius: 12px;
                padding: 3rem;
                background-color: #F0F8FF;
                margin: 2rem 0;
                min-width: 400px;
            }}
            
            .dialogue-container {{
                background-color: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin: 2rem auto;
                max-width: 600px;
            }}
            
            .dialogue-title {{
                font-size: 1.8rem;
                font-weight: bold;
                color: #2C5F8D;
                margin-bottom: 1.5rem;
                text-align: center;
                font-family: 'OpenDyslexic', Arial, sans-serif;
            }}
            
            .focus-content-container {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                padding: 2rem;
                max-width: 900px;
                margin: 0 auto;
            }}
            
            .chunk-container {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                margin: 2rem 0;
                padding: 2rem;
                background-color: #FAFAFA;
                border-radius: 8px;
                border-left: 4px solid #4A90E2;
            }}
            
            .chunk-title {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                font-size: 1.5rem;
                font-weight: bold;
                color: #2C5F8D;
                margin-bottom: 1rem;
            }}
            
            .chunk-content {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                font-size: 1.2rem;
                line-height: 2;
                color: #333;
                letter-spacing: 0.02em;
            }}
            
            .flashcard-container {{
                perspective: 1000px;
                margin: 2rem 0;
            }}
            
            .flashcard {{
                width: 100%;
                height: 300px;
                position: relative;
                transform-style: preserve-3d;
                transition: transform 0.6s;
                cursor: pointer;
            }}
            
            .flashcard.flipped {{
                transform: rotateY(180deg);
            }}
            
            .flashcard-front,
            .flashcard-back {{
                position: absolute;
                width: 100%;
                height: 100%;
                backface-visibility: hidden;
                border-radius: 12px;
                padding: 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'OpenDyslexic', Arial, sans-serif;
                font-size: 1.3rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            
            .flashcard-front {{
                background: linear-gradient(135deg, #4A90E2 0%, #63B3ED 100%);
                color: white;
            }}
            
            .flashcard-back {{
                background: white;
                color: #333;
                transform: rotateY(180deg);
                border: 2px solid #4A90E2;
            }}
            
            .timer-display {{
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: rgba(74, 144, 226, 0.9);
                color: white;
                padding: 1rem 2rem;
                border-radius: 8px;
                font-size: 1.5rem;
                font-weight: bold;
                z-index: 1000;
                font-family: 'OpenDyslexic', Arial, sans-serif;
            }}
            
            .exit-focus-btn {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }}
        </style>
        """, unsafe_allow_html=True)
        st.session_state.css_rendered = True


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    render_css()
    
    # Initialize new state variables with defaults (always, not just on first run)
    if 'document_uploaded' not in st.session_state:
        st.session_state.document_uploaded = False
    if 'document_text' not in st.session_state:
        st.session_state.document_text = None
    if 'location_set' not in st.session_state:
        st.session_state.location_set = False
    if 'feeling_set' not in st.session_state:
        st.session_state.feeling_set = False
    if 'show_study_config' not in st.session_state:
        st.session_state.show_study_config = False
    if 'in_focus_mode' not in st.session_state:
        st.session_state.in_focus_mode = False
    if 'study_content' not in st.session_state:
        st.session_state.study_content = None
    if 'content_type' not in st.session_state:
        st.session_state.content_type = None
    if 'study_duration' not in st.session_state:
        st.session_state.study_duration = None
    if 'current_sprint' not in st.session_state:
        st.session_state.current_sprint = None
    if 'audio_started' not in st.session_state:
        st.session_state.audio_started = False
    if 'current_flashcard_index' not in st.session_state:
        st.session_state.current_flashcard_index = 0
    if 'flashcards' not in st.session_state:
        st.session_state.flashcards = []
    if 'current_chunk_index' not in st.session_state:
        st.session_state.current_chunk_index = 0
    
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.state_manager = StateManager(user_id="default_user")
        
        with st.spinner("Loading knowledge base..."):
            st.session_state.kb_loader = KnowledgeBaseLoader()
            success = st.session_state.kb_loader.initialize()
            
            if not success:
                st.error("⚠️ Error loading knowledge base")
        
        st.session_state.rag_engine = RAGEngine(st.session_state.kb_loader)
        st.session_state.llm_orchestrator = LLMOrchestrator(
            st.session_state.rag_engine,
            st.session_state.state_manager
        )
        st.session_state.doc_handler = DocumentHandler()
        st.session_state.text_chunker = TextChunker()


def render_welcome_page():
    """Render the welcome page with document upload."""
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-title">🧠 NeuroLearn</div>
        <div class="welcome-subtitle">Your Adaptive Study Coach</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    st.markdown("### 📄 Upload Your Document")
    st.markdown("Upload the document you want to study")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'docx'],
        key="doc_upload",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        # Save temporarily
        temp_path = Path(f"/tmp/{uploaded_file.name}")
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.read())
        
        # Extract text
        with st.spinner("Extracting text from document..."):
            text = st.session_state.doc_handler.extract_text(str(temp_path))
        
        if text:
            st.session_state.document_text = text
            st.session_state.document_uploaded = True
            st.success("✅ Document uploaded successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Could not extract text from document")
        
        # Clean up
        temp_path.unlink(missing_ok=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_setup_dialogue():
    """Render dialogue asking about location and feeling."""
    st.markdown("""
    <div class="dialogue-container">
        <div class="dialogue-title">Let's Set Up Your Study Session</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Location
    st.markdown("### 📍 Where are you studying?")
    
    # Get current environment or default
    current_env = st.session_state.state_manager.state.get('current_environment', 'home')
    env_index = STUDY_ENVIRONMENTS.index(current_env) if current_env in STUDY_ENVIRONMENTS else 0
    
    location = st.selectbox(
        "Select your location:",
        STUDY_ENVIRONMENTS,
        index=env_index,
        key="location_select",
        label_visibility="collapsed"
    )
    
    # Update state immediately when changed
    if location:
        st.session_state.state_manager.update_environment(location)
        st.session_state.location_set = True
    
    st.markdown("---")
    
    # Feeling
    st.markdown("### 😊 How are you feeling?")
    
    # Get current focus state or default
    current_focus = st.session_state.state_manager.state.get('focus_state', 'neutral')
    focus_index = FOCUS_STATES.index(current_focus) if current_focus in FOCUS_STATES else 0
    
    feeling = st.selectbox(
        "Select how you're feeling:",
        FOCUS_STATES,
        index=focus_index,
        key="feeling_select",
        label_visibility="collapsed"
    )
    
    # Update state immediately when changed
    if feeling:
        st.session_state.state_manager.update_focus_state(feeling)
        st.session_state.feeling_set = True
    
    st.markdown("---")
    
    # Continue button
    if st.button("Continue →", use_container_width=True, type="primary"):
        if location and feeling:
            st.session_state.show_study_config = True  # Move to next step
            st.rerun()
        else:
            st.warning("Please select both location and feeling before continuing.")


def render_study_config():
    """Render study configuration (time and content type)."""
    st.markdown("""
    <div class="dialogue-container">
        <div class="dialogue-title">Configure Your Study Session</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Time selection
    st.markdown("### ⏱️ How long do you want to study?")
    
    # Get recommended duration based on focus state
    focus_state = st.session_state.state_manager.state.get('focus_state', 'neutral')
    recommended_duration = FocusSprint.get_recommended_duration(focus_state)
    
    # Display recommendation
    st.info(f"💡 **Recommended duration:** {recommended_duration} minutes (based on your current focus state: {focus_state})")
    
    duration = st.number_input(
        "Duration (minutes):",
        min_value=2,
        max_value=60,
        value=recommended_duration,
        step=1,
        key="duration_input",
        label_visibility="collapsed"
    )
    
    st.session_state.study_duration = duration
    
    st.markdown("---")
    
    # Content type selection
    st.markdown("### 📚 What would you like to study?")
    content_type = st.radio(
        "Choose an option:",
        ["Summary", "Flashcards", "Whole Text"],
        key="content_type_radio",
        label_visibility="collapsed"
    )
    
    st.session_state.content_type = content_type.lower()
    
    st.markdown("---")
    
    # Only show start button if content hasn't been generated yet
    # Also check if we're not already in focus mode
    if not st.session_state.study_content and not st.session_state.flashcards and not st.session_state.in_focus_mode:
        # Start button
        if st.button("🚀 Start Focus Mode", use_container_width=True, type="primary"):
            # Process document based on content type
            with st.spinner("Preparing your study content..."):
                if content_type.lower() == "summary":
                    focus_state = st.session_state.state_manager.state.get('focus_state', 'neutral')
                    summary_prompt = st.session_state.doc_handler.create_summary_prompt(
                        st.session_state.document_text[:10000],
                        focus_state=focus_state
                    )
                    response_data = st.session_state.llm_orchestrator.generate_response(
                        summary_prompt,
                        max_tokens=2000
                    )
                    summary = response_data.get('response', '')
                    
                    if not summary or len(summary.strip()) == 0:
                        st.error("Failed to generate summary. Please try again.")
                        st.stop()
                    
                    # Chunk the summary text (like Full Text used to do)
                    chunks = st.session_state.text_chunker.chunk_text_with_llm(
                        summary,
                        focus_state=focus_state
                    )
                    if chunks and len(chunks) > 0:
                        st.session_state.study_content = chunks
                    else:
                        # Fallback to single chunk
                        st.session_state.study_content = [{
                            "title": "Summary",
                            "type": "summary",
                            "content": summary
                        }]
                
                elif content_type.lower() == "flashcards":
                    # Generate flashcards
                    flashcard_prompt = f"""Create flashcards from the following text. For each important concept, create a flashcard with:
- Front: A question or term
- Back: The answer or definition

Format your response EXACTLY like this:
FLASHCARD 1
Front: [question or term]
Back: [answer or definition]

FLASHCARD 2
Front: [question or term]
Back: [answer or definition]

Text to create flashcards from:
{st.session_state.document_text[:5000]}

Create at least 5-10 flashcards covering the most important concepts."""
                    
                    response_data = st.session_state.llm_orchestrator.generate_response(
                        flashcard_prompt,
                        max_tokens=2000
                    )
                    flashcard_text = response_data.get('response', '')
                    
                    if not flashcard_text or len(flashcard_text.strip()) == 0:
                        st.error("Failed to generate flashcards. Using fallback method.")
                        # Fallback: create simple flashcards
                        sentences = st.session_state.document_text.split('.')[:10]
                        flashcards = [
                            {"front": f"Key Point {i+1}", "back": s.strip()}
                            for i, s in enumerate(sentences) if s.strip()
                        ]
                    else:
                        # Parse flashcards
                        flashcards = []
                        current_card = {}
                        for line in flashcard_text.split('\n'):
                            line = line.strip()
                            if line.startswith('FLASHCARD') or line == '':
                                if current_card.get('front') and current_card.get('back'):
                                    flashcards.append(current_card)
                                current_card = {}
                            elif line.startswith('Front:'):
                                current_card['front'] = line.replace('Front:', '').strip()
                            elif line.startswith('Back:'):
                                current_card['back'] = line.replace('Back:', '').strip()
                        
                        if current_card.get('front') and current_card.get('back'):
                            flashcards.append(current_card)
                        
                        if not flashcards:
                            # Fallback: create simple flashcards
                            sentences = st.session_state.document_text.split('.')[:10]
                            flashcards = [
                                {"front": f"Key Point {i+1}", "back": s.strip()}
                                for i, s in enumerate(sentences) if s.strip()
                            ]
                    
                    if not flashcards:
                        st.error("Could not create flashcards. Please try again.")
                        st.stop()
                    
                    st.session_state.flashcards = flashcards
                    st.session_state.study_content = flashcards
                
                else:  # whole text
                    # Display the original full text without chunking
                    st.session_state.study_content = [{
                        "title": "Full Text",
                        "type": "full_text",
                        "content": st.session_state.document_text
                    }]
            
            # Start focus mode
            st.session_state.in_focus_mode = True
            st.session_state.current_sprint = FocusSprint(duration_minutes=duration)
            st.session_state.current_sprint.start()
            st.session_state.state_manager.start_sprint(
                duration_minutes=duration,
                task_description=f"Study {content_type}"
            )
            st.rerun()
    # If content already exists, don't show the button - user should already be in focus mode


def render_focus_mode():
    """Render focus mode - minimal UI with only study content."""
    # Inject CSS to hide distracting elements and add white overlay
    st.markdown("""
    <script>
        if (!document.body.classList.contains('focus-mode')) {
            document.body.classList.add('focus-mode');
        }
        // Hide sidebar if visible
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) sidebar.style.display = 'none';
        // Hide header
        const header = document.querySelector('header');
        if (header) header.style.display = 'none';
        // Hide footer
        const footer = document.querySelector('footer');
        if (footer) footer.style.display = 'none';
        
        // Add white overlay
        let overlay = document.getElementById('white-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'white-overlay';
            overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: white; z-index: 999999; transition: opacity 0.5s ease-out;';
            document.body.appendChild(overlay);
            
            // Fade out overlay after a short delay
            setTimeout(() => {
                overlay.style.opacity = '0';
                setTimeout(() => {
                    overlay.remove();
                }, 500);
            }, 300);
        }
    </script>
    <style>
        .focus-mode header,
        .focus-mode footer,
        .focus-mode [data-testid="stSidebar"],
        .focus-mode [data-testid="stToolbar"],
        .focus-mode [data-testid="stDecoration"],
        .focus-mode [data-testid="stStatusWidget"] {
            display: none !important;
        }
        
        #white-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: white;
            z-index: 999999;
            transition: opacity 0.5s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Start brown noise audio
    if not st.session_state.audio_started:
        audio_path = Path(__file__).parent.parent / "font" / "soothing-brown-noise-with-asmr-crinkles-304896.mp3"
        if audio_path.exists():
            audio_base64 = get_audio_base64(audio_path)
            audio_html = f"""
            <audio id="focus-audio" autoplay loop style="display: none;" preload="auto">
                <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
            </audio>
            <script>
                (function() {{
                    // Wait for DOM to be ready
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', initAudio);
                    }} else {{
                        initAudio();
                    }}
                    
                    function initAudio() {{
                        let audio = document.getElementById('focus-audio');
                        if (!audio) {{
                            // Create audio element if it doesn't exist
                            audio = document.createElement('audio');
                            audio.id = 'focus-audio';
                            audio.loop = true;
                            audio.style.display = 'none';
                            audio.preload = 'auto';
                            audio.volume = 0.5;
                            const source = document.createElement('source');
                            source.src = 'data:audio/mpeg;base64,{audio_base64}';
                            source.type = 'audio/mpeg';
                            audio.appendChild(source);
                            document.body.appendChild(audio);
                        }}
                        
                        // Try to play
                        const playPromise = audio.play();
                        if (playPromise !== undefined) {{
                            playPromise.catch(function(error) {{
                                console.log('Autoplay blocked:', error);
                                // Try again on any user interaction
                                const playOnInteraction = function() {{
                                    audio.play().catch(function(e) {{
                                        console.log('Audio play failed:', e);
                                    }});
                                    document.removeEventListener('click', playOnInteraction);
                                    document.removeEventListener('touchstart', playOnInteraction);
                                    document.removeEventListener('keydown', playOnInteraction);
                                }};
                                document.addEventListener('click', playOnInteraction, {{ once: true }});
                                document.addEventListener('touchstart', playOnInteraction, {{ once: true }});
                                document.addEventListener('keydown', playOnInteraction, {{ once: true }});
                            }});
                        }}
                    }}
                }})();
            </script>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        st.session_state.audio_started = True
    
    # Timer display (always show if sprint exists)
    if st.session_state.current_sprint:
        sprint = st.session_state.current_sprint
        if not sprint.is_finished():
            remaining = sprint.format_time_remaining()
            st.markdown(f'<div class="timer-display">⏱️ {remaining}</div>', unsafe_allow_html=True)
        else:
            # Session finished
            st.markdown("""
            <div class="focus-content-container">
                <h1 style="text-align: center; color: #4A90E2;">🎉 Study Session Complete!</h1>
                <p style="text-align: center; font-size: 1.2rem;">Great job staying focused!</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Exit Focus Mode", use_container_width=True, key="exit_focus"):
                st.session_state.in_focus_mode = False
                st.session_state.audio_started = False
                st.session_state.current_sprint = None
                st.session_state.state_manager.complete_sprint(successful=True)
                st.rerun()
            return
    
    # Render study content based on type
    if not st.session_state.study_content and not st.session_state.flashcards:
        st.error("No study content available. Please go back and regenerate your content.")
        if st.button("Exit Focus Mode", use_container_width=True, key="exit_no_content"):
            st.session_state.in_focus_mode = False
            st.session_state.audio_started = False
            st.rerun()
        return
    
    if st.session_state.content_type == "flashcards":
        render_flashcards()
    else:
        render_text_content()
    
    # Auto-refresh timer if sprint is active
    if st.session_state.current_sprint and not st.session_state.current_sprint.is_finished():
        time.sleep(1)
        st.rerun()
    
    # Exit button
    if st.button("Exit Focus Mode", use_container_width=True, key="exit_focus_btn"):
        st.session_state.in_focus_mode = False
        st.session_state.audio_started = False
        if st.session_state.current_sprint:
            st.session_state.state_manager.complete_sprint(successful=False)
            st.session_state.current_sprint = None
        st.rerun()


def render_flashcards():
    """Render flashcards in focus mode."""
    if not st.session_state.flashcards:
        st.error("No flashcards available")
        return
    
    if 'current_flashcard_index' not in st.session_state:
        st.session_state.current_flashcard_index = 0
    
    current_index = st.session_state.current_flashcard_index
    total_flashcards = len(st.session_state.flashcards)
    
    if current_index >= total_flashcards:
        st.session_state.current_flashcard_index = 0
        current_index = 0
    
    current_card = st.session_state.flashcards[current_index]
    
    # Track flip state
    if 'flashcard_flipped' not in st.session_state:
        st.session_state.flashcard_flipped = False
    
    # Escape HTML content
    front_text = html.escape(current_card.get('front', 'Question'))
    back_text = html.escape(current_card.get('back', 'Answer'))
    
    # Flashcard HTML with embedded styles
    flipped_class = "flipped" if st.session_state.flashcard_flipped else ""
    flashcard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'OpenDyslexic', Arial, sans-serif;
            }}
            
            .focus-content-container {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                padding: 2rem;
                max-width: 900px;
                margin: 0 auto;
            }}
            
            .flashcard-container {{
                perspective: 1000px;
                margin: 2rem auto;
                width: 100%;
                max-width: 600px;
            }}
            
            .flashcard {{
                width: 100%;
                height: 400px;
                position: relative;
                transform-style: preserve-3d;
                transition: transform 0.6s ease;
            }}
            
            .flashcard.flipped {{
                transform: rotateY(180deg);
            }}
            
            .flashcard-front,
            .flashcard-back {{
                position: absolute;
                width: 100%;
                height: 100%;
                backface-visibility: hidden;
                -webkit-backface-visibility: hidden;
                border-radius: 12px;
                padding: 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'OpenDyslexic', Arial, sans-serif;
                box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            }}
            
            .flashcard-front {{
                background: linear-gradient(135deg, #4A90E2 0%, #63B3ED 100%);
                color: white;
                transform: rotateY(0deg);
            }}
            
            .flashcard-back {{
                background: white;
                color: #333;
                transform: rotateY(180deg);
                border: 3px solid #4A90E2;
            }}
            
            .flashcard-content {{
                text-align: center;
                padding: 1rem;
                width: 100%;
            }}
            
            .flashcard-front h2 {{
                margin: 0;
                font-size: 1.8rem;
                font-weight: bold;
                color: white;
                margin-bottom: 1rem;
            }}
            
            .flashcard-front .hint {{
                margin-top: 1.5rem;
                font-size: 0.9rem;
                opacity: 0.9;
            }}
            
            .flashcard-back p {{
                font-size: 1.3rem;
                line-height: 1.8;
                color: #333;
                margin: 0;
            }}
            
            .card-counter {{
                text-align: center;
                margin-top: 2rem;
                font-size: 1.1rem;
                color: #666;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="focus-content-container">
            <div class="flashcard-container">
                <div class="flashcard {flipped_class}" id="flashcard">
                    <div class="flashcard-front">
                        <div class="flashcard-content">
                            <h2>{front_text}</h2>
                            <p class="hint">Click "Flip Card" to see the answer</p>
                        </div>
                    </div>
                    <div class="flashcard-back">
                        <div class="flashcard-content">
                            <p>{back_text}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card-counter">
                Card {current_index + 1} of {total_flashcards}
            </div>
        </div>
    </body>
    </html>
    """
    
    components.html(flashcard_html, height=550, scrolling=False)
    
    # Progress bar for flashcards
    progress_percentage = ((current_index + 1) / total_flashcards) * 100
    remaining_cards = total_flashcards - (current_index + 1)
    st.progress(progress_percentage / 100)
    st.caption(f"📊 Progress: {current_index + 1}/{total_flashcards} cards ({remaining_cards} remaining)")
    
    # Navigation buttons - use 3 columns with equal spacing for better alignment
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_index == 0), use_container_width=True, key="flashcard_prev"):
            if current_index > 0:
                st.session_state.current_flashcard_index = current_index - 1
                st.session_state.flashcard_flipped = False  # Reset flip state
                st.rerun()
    
    with col2:
        if st.button("🔄 Flip Card", use_container_width=True, key="flashcard_flip"):
            st.session_state.flashcard_flipped = not st.session_state.flashcard_flipped
            st.rerun()
    
    with col3:
        if st.button("Next ➡️", use_container_width=True, key="flashcard_next"):
            new_index = current_index + 1
            if new_index >= total_flashcards:
                st.session_state.current_flashcard_index = 0
            else:
                st.session_state.current_flashcard_index = new_index
            st.session_state.flashcard_flipped = False  # Reset flip state
            st.rerun()


def render_text_content():
    """Render text content (summary or whole text) in focus mode."""
    if not st.session_state.study_content:
        st.error("No content available")
        return
    
    if 'current_chunk_index' not in st.session_state:
        st.session_state.current_chunk_index = 0
    
    current_index = st.session_state.current_chunk_index
    total_chunks = len(st.session_state.study_content)
    
    if current_index >= total_chunks:
        st.session_state.current_chunk_index = 0
        current_index = 0
    
    current_chunk = st.session_state.study_content[current_index]
    chunk_type = current_chunk.get('type', 'main_point')
    title = current_chunk.get('title', f'Section {current_index+1}')
    content = current_chunk.get('content', '')
    
    if not content or len(content.strip()) == 0:
        st.warning(f"Content for section '{title}' is empty.")
        return
    
    # Clean content - remove any HTML tags that might be in the LLM response
    # and escape to prevent XSS
    # Remove HTML tags from content (in case LLM included them)
    clean_content = re.sub(r'<[^>]+>', '', content)
    # Escape HTML entities
    escaped_content = html.escape(clean_content)
    # Convert line breaks to <br> tags
    escaped_content = escaped_content.replace('\n', '<br>')
    
    # Render chunk using components.html for better rendering
    chunk_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .focus-content-container {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                padding: 2rem;
                max-width: 900px;
                margin: 0 auto;
            }}
            .chunk-container {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                margin: 2rem 0;
                padding: 2rem;
                background-color: #FAFAFA;
                border-radius: 8px;
                border-left: 4px solid #4A90E2;
            }}
            .chunk-title {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                font-size: 1.5rem;
                font-weight: bold;
                color: #2C5F8D;
                margin-bottom: 1rem;
            }}
            .chunk-content {{
                font-family: 'OpenDyslexic', Arial, sans-serif;
                font-size: 1.2rem;
                line-height: 2;
                color: #333;
                letter-spacing: 0.02em;
            }}
        </style>
    </head>
    <body>
        <div class="focus-content-container">
            <div class="chunk-container chunk-{html.escape(chunk_type)}">
                <div class="chunk-title">{html.escape(title)}</div>
                <div class="chunk-content">{escaped_content}</div>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <p style="font-size: 1.1rem; color: #666;">Section {current_index + 1} of {total_chunks}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    components.html(chunk_html, height=600, scrolling=True)
    
    # Progress bar for Summary mode (only show if it's summary type and has multiple chunks)
    if chunk_type == 'summary' and total_chunks > 1:
        progress_percentage = ((current_index + 1) / total_chunks) * 100
        remaining_chunks = total_chunks - (current_index + 1)
        st.progress(progress_percentage / 100)
        st.caption(f"📊 Progress: {current_index + 1}/{total_chunks} sections ({remaining_chunks} remaining)")
    
    # Show navigation buttons when there are multiple chunks
    # Both Summary and Full Text are now chunked, so show buttons for any chunked content
    if total_chunks > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=(current_index == 0), use_container_width=True):
                st.session_state.current_chunk_index -= 1
                st.rerun()
        
        with col3:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_chunk_index += 1
                if st.session_state.current_chunk_index >= total_chunks:
                    st.session_state.current_chunk_index = 0
                st.rerun()


def render_sidebar():
    """Render sidebar with session statistics."""
    with st.sidebar:
        st.markdown("### 📊 Study Statistics")
        st.markdown("---")
        
        # Get completed sessions count
        completed_sessions = st.session_state.state_manager.state.get("successful_sprints", 0)
        total_sprints = st.session_state.state_manager.state.get("sprint_count", 0)
        total_focus_time = st.session_state.state_manager.state.get("total_focus_time_minutes", 0)
        
        st.metric("✅ Completed Sessions", completed_sessions)
        
        if total_sprints > 0:
            st.caption(f"Total sprints started: {total_sprints}")
        
        if total_focus_time > 0:
            hours = total_focus_time // 60
            minutes = total_focus_time % 60
            if hours > 0:
                st.caption(f"Total focus time: {hours}h {minutes}m")
            else:
                st.caption(f"Total focus time: {minutes}m")


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render sidebar (except in focus mode where it's hidden)
    if not st.session_state.in_focus_mode:
        render_sidebar()
    
    # Determine which page to show
    if st.session_state.in_focus_mode:
        render_focus_mode()
    elif (st.session_state.study_content or st.session_state.flashcards) and not st.session_state.in_focus_mode:
        # If content exists but we're not in focus mode, automatically enter focus mode
        st.session_state.in_focus_mode = True
        if not st.session_state.current_sprint and st.session_state.study_duration:
            st.session_state.current_sprint = FocusSprint(duration_minutes=st.session_state.study_duration)
            st.session_state.current_sprint.start()
        render_focus_mode()
    elif st.session_state.show_study_config:
        render_study_config()
    elif st.session_state.document_uploaded:
        render_setup_dialogue()
    else:
        render_welcome_page()


# Streamlit runs this script on every rerun
main()
