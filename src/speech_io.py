"""
Speech I/O Module
Handles speech-to-text (Whisper) and text-to-speech (pyttsx3) functionality.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import sounddevice as sd
import soundfile as sf
import numpy as np

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available - STT disabled")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("pyttsx3 not available - TTS disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeechIO:
    """Handles speech input and output for hands-free interaction."""
    
    def __init__(
        self,
        whisper_model_size: str = "base",
        sample_rate: int = 16000
    ):
        """
        Initialize speech I/O.
        
        Args:
            whisper_model_size: Whisper model size (tiny, base, small, medium, large)
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self.whisper_model = None
        self.tts_engine = None
        
        # Initialize Whisper (lazy loading)
        if WHISPER_AVAILABLE:
            self.whisper_model_size = whisper_model_size
            logger.info(f"Speech recognition enabled (Whisper {whisper_model_size})")
        else:
            logger.warning("Speech recognition not available")
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self._configure_tts()
                logger.info("Text-to-speech enabled")
            except Exception as e:
                logger.error(f"Error initializing TTS: {e}")
                self.tts_engine = None  # Reset on error
        else:
            logger.warning("Text-to-speech not available")
    
    def _configure_tts(self):
        """Configure TTS engine properties."""
        if not self.tts_engine:
            return
        
        # Set properties for clear, calm speech
        self.tts_engine.setProperty('rate', 150)  # Slower speech
        self.tts_engine.setProperty('volume', 0.9)
        
        # Try to use a pleasant voice
        voices = self.tts_engine.getProperty('voices')
        if voices:
            # Prefer female voice if available (often perceived as calmer)
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
    
    def _load_whisper_model(self):
        """Lazy load Whisper model."""
        if not WHISPER_AVAILABLE:
            return False
        
        if self.whisper_model is None:
            try:
                logger.info(f"Loading Whisper model: {self.whisper_model_size}")
                self.whisper_model = whisper.load_model(self.whisper_model_size)
                logger.info("Whisper model loaded")
                return True
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                return False
        return True
    
    def record_audio(self, duration_seconds: int = 5) -> Optional[np.ndarray]:
        """
        Record audio from microphone.
        
        Args:
            duration_seconds: Recording duration
            
        Returns:
            Audio data as numpy array or None
        """
        try:
            logger.info(f"Recording audio for {duration_seconds} seconds...")
            audio_data = sd.rec(
                int(duration_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()  # Wait for recording to complete
            logger.info("Recording complete")
            return audio_data
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
    
    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcribed text or None
        """
        if not WHISPER_AVAILABLE or not self._load_whisper_model():
            logger.error("Whisper not available")
            return None
        
        try:
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_path = temp_audio.name
                sf.write(temp_path, audio_data, self.sample_rate)
            
            # Transcribe
            logger.info("Transcribing audio...")
            result = self.whisper_model.transcribe(temp_path)
            text = result.get('text', '').strip()
            
            # Clean up temp file
            Path(temp_path).unlink()
            
            logger.info(f"Transcription: {text[:50]}...")
            return text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    def speech_to_text(self, duration_seconds: int = 5) -> Optional[str]:
        """
        Record audio and transcribe to text.
        
        Args:
            duration_seconds: Recording duration
            
        Returns:
            Transcribed text or None
        """
        audio_data = self.record_audio(duration_seconds)
        if audio_data is None:
            return None
        
        return self.transcribe_audio(audio_data)
    
    def text_to_speech(self, text: str, blocking: bool = True) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            blocking: Wait for speech to complete
            
        Returns:
            True if successful
        """
        if not self.tts_engine:
            logger.error("TTS not available")
            return False
        
        try:
            logger.info(f"Speaking: {text[:50]}...")
            self.tts_engine.say(text)
            
            if blocking:
                self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            return False
    
    def speak_encouragement(self, focus_state: str = "neutral") -> bool:
        """
        Speak an encouraging message based on focus state.
        
        Args:
            focus_state: Current focus state
            
        Returns:
            True if successful
        """
        messages = {
            "overwhelmed": "Take a deep breath. You've got this. Let's start with just one small step.",
            "distracted": "Let's refocus together. Pick one tiny task to start with.",
            "focused": "You're doing great! Keep that momentum going.",
            "neutral": "Ready to make some progress? I'm here to help."
        }
        
        message = messages.get(focus_state, messages["neutral"])
        return self.text_to_speech(message)
    
    def is_stt_available(self) -> bool:
        """Check if speech-to-text is available."""
        return WHISPER_AVAILABLE and self._load_whisper_model()
    
    def is_tts_available(self) -> bool:
        """Check if text-to-speech is available."""
        return self.tts_engine is not None

