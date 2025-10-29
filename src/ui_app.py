"""
NeuroLearn Streamlit UI
Main user interface for the adaptive study coach.
"""

import streamlit as st
import time
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
from speech_io import SpeechIO


# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4A90E2;
        text-align: center;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .disclaimer {
        background-color: #FFF3CD;
        border-left: 4px solid #FFC107;
        padding: 0.75rem;
        margin: 1rem 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .focus-state-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .sprint-timer {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        color: #4A90E2;
        padding: 1rem;
        background-color: #F0F8FF;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.state_manager = StateManager(user_id="default_user")
        
        # Initialize knowledge base
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
        st.session_state.speech_io = SpeechIO()
        
        st.session_state.current_sprint = None
        st.session_state.messages = []
        st.session_state.show_sprint_timer = False


def render_header():
    """Render app header with title and disclaimer."""
    st.markdown(f'<div class="main-header">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="disclaimer">ℹ️ {DISCLAIMER}</div>', unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with controls and status."""
    with st.sidebar:
        st.header("⚙️ Session Controls")
        
        # Get current state
        state_summary = st.session_state.state_manager.get_state_summary()
        
        # Focus state selector
        st.subheader("How are you feeling?")
        current_focus = state_summary.get('focus_state', 'neutral')
        
        focus_state = st.selectbox(
            "Select your focus state:",
            FOCUS_STATES,
            index=FOCUS_STATES.index(current_focus),
            key="focus_state_selector"
        )
        
        if focus_state != current_focus:
            st.session_state.state_manager.update_focus_state(focus_state)
            st.success(f"Focus state updated to: {focus_state}")
        
        # Environment selector
        st.subheader("Where are you studying?")
        current_env = state_summary.get('environment', 'home')
        
        environment = st.selectbox(
            "Study environment:",
            STUDY_ENVIRONMENTS,
            index=STUDY_ENVIRONMENTS.index(current_env) if current_env in STUDY_ENVIRONMENTS else 0,
            key="environment_selector"
        )
        
        if environment != current_env:
            st.session_state.state_manager.update_environment(environment)
        
        st.divider()
        
        # Session statistics
        st.subheader("📊 Your Progress")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Sprints", f"{state_summary['successful_sprints']}/{state_summary['sprint_count']}")
        
        with col2:
            st.metric("Focus Time", f"{state_summary['total_focus_time']} min")
        
        # Recent successful strategies
        if state_summary.get('recent_successful_strategies'):
            st.subheader("✨ What worked for you:")
            for strategy in state_summary['recent_successful_strategies'][:3]:
                st.write(f"• {strategy}")


def render_focus_sprint_controls():
    """Render focus sprint timer and controls."""
    st.subheader("⏱️ Focus Sprint")
    
    state_summary = st.session_state.state_manager.get_state_summary()
    
    # Check if there's an active sprint
    if st.session_state.state_manager.state.get('current_sprint'):
        sprint_data = st.session_state.state_manager.state['current_sprint']
        
        if not sprint_data.get('completed', False):
            # Active sprint
            if st.session_state.current_sprint is None:
                # Recreate sprint object from saved data
                st.session_state.current_sprint = FocusSprint(sprint_data['duration_minutes'])
                st.session_state.current_sprint.start_time = datetime.fromisoformat(sprint_data['start_time'])
                st.session_state.current_sprint.is_active = True
                st.session_state.current_sprint.task_description = sprint_data.get('task_description', '')
            
            sprint = st.session_state.current_sprint
            
            # Display timer
            if sprint.is_finished():
                st.success("🎉 Sprint completed! How did it go?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Successful", use_container_width=True):
                        st.session_state.state_manager.complete_sprint(successful=True)
                        st.session_state.current_sprint = None
                        st.rerun()
                
                with col2:
                    if st.button("❌ Incomplete", use_container_width=True):
                        st.session_state.state_manager.complete_sprint(successful=False)
                        st.session_state.current_sprint = None
                        st.rerun()
            else:
                # Show countdown
                remaining = sprint.format_time_remaining()
                st.markdown(f'<div class="sprint-timer">{remaining}</div>', unsafe_allow_html=True)
                
                progress = sprint.get_progress_percentage()
                st.progress(progress / 100)
                
                if sprint.task_description:
                    st.info(f"📝 Working on: {sprint.task_description}")
                
                if st.button("⏹️ Stop Sprint"):
                    st.session_state.state_manager.complete_sprint(successful=False)
                    st.session_state.current_sprint = None
                    st.rerun()
                
                # Auto-refresh every second
                time.sleep(1)
                st.rerun()
        else:
            st.session_state.current_sprint = None
    
    else:
        # No active sprint - show start controls
        focus_state = state_summary.get('focus_state', 'neutral')
        recommended_duration = FocusSprint.get_recommended_duration(focus_state)
        
        st.info(f"💡 Recommended sprint: {recommended_duration} minutes based on your current state")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            task_description = st.text_input(
                "What will you work on?",
                placeholder="e.g., Read chapter 3, write introduction...",
                key="sprint_task"
            )
        
        with col2:
            duration = st.number_input(
                "Minutes",
                min_value=5,
                max_value=25,
                value=recommended_duration,
                step=5,
                key="sprint_duration"
            )
        
        if st.button("🚀 Start Sprint", use_container_width=True):
            # Start new sprint
            sprint = FocusSprint(duration_minutes=duration)
            sprint.start(task_description=task_description)
            
            st.session_state.current_sprint = sprint
            st.session_state.state_manager.start_sprint(
                duration_minutes=duration,
                task_description=task_description
            )
            
            st.success(f"Sprint started! Focus for {duration} minutes.")
            time.sleep(1)
            st.rerun()


def render_chat_interface():
    """Render the chat interface."""
    st.subheader("💬 Chat with NeuroLearn")
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask me anything about studying, focus, or planning...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data = st.session_state.llm_orchestrator.generate_response(user_input)
                response_text = response_data.get('response', "I'm here to help!")
                
                st.write(response_text)
                
                # Show strategies used (if any)
                strategies_used = response_data.get('strategies_used', [])
                if strategies_used:
                    with st.expander("📚 Strategies used"):
                        for strategy in strategies_used:
                            st.write(f"• {strategy}")
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})


def render_document_upload():
    """Render document upload and processing section."""
    with st.expander("📄 Upload Document for Help"):
        st.write("Upload a PDF or text file for summarization or study support")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'txt', 'docx'],
            key="doc_upload"
        )
        
        if uploaded_file:
            # Save temporarily
            temp_path = Path(f"/tmp/{uploaded_file.name}")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())
            
            # Extract text
            with st.spinner("Extracting text..."):
                text = st.session_state.doc_handler.extract_text(str(temp_path))
            
            if text:
                # Show stats
                stats = st.session_state.doc_handler.get_document_stats(text)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Words", stats['word_count'])
                with col2:
                    st.metric("Est. Reading Time", f"{stats['estimated_reading_time_minutes']} min")
                with col3:
                    st.metric("Characters", stats['character_count'])
                
                # Summarize button
                if st.button("✨ Summarize This"):
                    focus_state = st.session_state.state_manager.state.get('focus_state', 'neutral')
                    
                    # Create summary prompt
                    summary_prompt = st.session_state.doc_handler.create_summary_prompt(
                        text[:3000],  # Limit for speed
                        focus_state=focus_state
                    )
                    
                    with st.spinner("Creating summary..."):
                        response_data = st.session_state.llm_orchestrator.generate_response(
                            summary_prompt,
                            max_tokens=500
                        )
                        summary = response_data.get('response', '')
                    
                    st.success("Summary:")
                    st.write(summary)
                    
                    # Add to chat
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"Summarize: {uploaded_file.name}"
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": summary
                    })
            else:
                st.error("Could not extract text from document")
            
            # Clean up
            temp_path.unlink(missing_ok=True)


def render_reflection_form():
    """Render post-session reflection form."""
    with st.expander("🤔 Reflect on Your Session"):
        st.write("Take a moment to log how this session went")
        
        rating = st.slider(
            "How focused did you feel? (1=very distracted, 5=very focused)",
            min_value=1,
            max_value=5,
            value=3,
            key="focus_rating"
        )
        
        what_helped = st.text_area(
            "What helped the most?",
            placeholder="e.g., short timer, clear steps, quiet environment...",
            key="what_helped"
        )
        
        if st.button("💾 Save Reflection"):
            st.session_state.state_manager.add_focus_rating(
                rating=rating,
                what_helped=what_helped
            )
            st.success("✅ Reflection saved! I'll remember this for next time.")


def main():
    """Main application entry point."""
    init_session_state()
    
    render_header()
    render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_chat_interface()
        render_document_upload()
    
    with col2:
        render_focus_sprint_controls()
        st.divider()
        render_reflection_form()


if __name__ == "__main__":
    main()

