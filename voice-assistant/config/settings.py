"""
Central configuration module.
Loads all settings from environment variables with sensible defaults.
Must be imported before any other module that needs config.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")


class AudioConfig:
    # PyAudio device indices
    INPUT_DEVICE_INDEX: int = int(os.getenv("AUDIO_INPUT_DEVICE_INDEX", "0"))
    OUTPUT_DEVICE_INDEX: int = int(os.getenv("AUDIO_OUTPUT_DEVICE_INDEX", "0"))

    # Recording parameters
    SAMPLE_RATE: int = 16000       # 16kHz required by webrtcvad and Google STT
    CHANNELS: int = 1              # Mono capture from one mic channel
    SAMPLE_WIDTH: int = 2          # 16-bit PCM = 2 bytes
    FORMAT: int = 8                # pyaudio.paInt16 = 8

    # VAD parameters
    VAD_AGGRESSIVENESS: int = int(os.getenv("VAD_AGGRESSIVENESS", "2"))
    # Frame duration must be 10, 20, or 30ms for webrtcvad
    VAD_FRAME_MS: int = 30
    # Number of silent frames after speech before we stop recording
    SILENCE_FRAMES_THRESHOLD: int = int(os.getenv("SILENCE_FRAMES_THRESHOLD", "33"))
    # ~1 second of silence at 30ms frames = 33 frames


class STTConfig:
    # Google Cloud STT
    LANGUAGE_CODE: str = os.getenv("STT_LANGUAGE_CODE", "en-US")
    # Use WEBM_OPUS or LINEAR16 (we send raw PCM)
    MODEL: str = os.getenv("STT_MODEL", "latest_long")


class TTSConfig:
    # Google Cloud TTS
    LANGUAGE_CODE: str = os.getenv("TTS_LANGUAGE_CODE", "en-US")
    VOICE_NAME: str = os.getenv("TTS_VOICE_NAME", "en-US-Neural2-J")
    SPEAKING_RATE: float = float(os.getenv("TTS_SPEAKING_RATE", "1.0"))
    PITCH: float = float(os.getenv("TTS_PITCH", "0.0"))


class AgentConfig:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    MAX_TOKENS: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "10"))
    SYSTEM_PROMPT: str = os.getenv(
        "SYSTEM_PROMPT",
        (
            "You are a helpful voice assistant running on a ReSpeaker device. "
            "Keep your responses concise and conversational — spoken aloud, so "
            "avoid markdown, bullet points, or special characters. "
            "Respond in plain, natural language as if speaking to someone in the room."
        ),
    )


class TriggerConfig:
    MODE: str = os.getenv("TRIGGER_MODE", "keyboard")  # 'button' or 'keyboard'
    BUTTON_GPIO_PIN: int = int(os.getenv("BUTTON_GPIO_PIN", "17"))


class Settings:
    audio = AudioConfig()
    stt = STTConfig()
    tts = TTSConfig()
    agent = AgentConfig()
    trigger = TriggerConfig()


settings = Settings()
