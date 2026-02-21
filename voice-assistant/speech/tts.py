"""
Google Cloud Text-to-Speech integration.

Sends text and returns MP3 bytes for playback.
"""
from google.cloud import texttospeech
from config.settings import settings


class TextToSpeech:
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
        cfg = settings.tts

        self.voice = texttospeech.VoiceSelectionParams(
            language_code=cfg.LANGUAGE_CODE,
            name=cfg.VOICE_NAME,
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=cfg.SPEAKING_RATE,
            pitch=cfg.PITCH,
        )

    def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: Plain text to synthesize (no markdown or special chars)

        Returns:
            MP3 audio bytes
        """
        if not text.strip():
            return b""

        input_text = texttospeech.SynthesisInput(text=text)

        print(f"[TTS] Synthesizing: {text[:60]}{'...' if len(text) > 60 else ''}")
        response = self.client.synthesize_speech(
            input=input_text,
            voice=self.voice,
            audio_config=self.audio_config,
        )

        print(f"[TTS] Received {len(response.audio_content)} bytes of MP3 audio.")
        return response.audio_content
