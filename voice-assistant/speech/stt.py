"""
Google Cloud Speech-to-Text integration.

Sends raw PCM audio bytes and returns the transcript text.

The audio from capture.py is already:
  - 16-bit signed PCM
  - 16000 Hz sample rate
  - Mono

This matches Google STT's LINEAR16 encoding requirement exactly.
"""
from google.cloud import speech
from config.settings import settings


class SpeechToText:
    def __init__(self):
        # Authentication via GOOGLE_APPLICATION_CREDENTIALS env var
        self.client = speech.SpeechClient()
        cfg = settings.stt

        self.recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=settings.audio.SAMPLE_RATE,
            language_code=cfg.LANGUAGE_CODE,
            model=cfg.MODEL,
            # Improve accuracy for voice assistant use
            enable_automatic_punctuation=True,
            use_enhanced=True,
        )

    def transcribe(self, pcm_audio: bytes) -> str:
        """
        Transcribe a complete audio utterance.

        Args:
            pcm_audio: Raw 16-bit mono PCM bytes at 16000 Hz

        Returns:
            Transcript string, or empty string if nothing recognized.
        """
        audio = speech.RecognitionAudio(content=pcm_audio)

        print(f"[STT] Sending {len(pcm_audio)} bytes to Google STT...")
        response = self.client.recognize(
            config=self.recognition_config, audio=audio
        )

        if not response.results:
            print("[STT] No speech recognized.")
            return ""

        # Take the highest-confidence result from the first alternative
        transcript = response.results[0].alternatives[0].transcript
        confidence = response.results[0].alternatives[0].confidence
        print(f"[STT] Transcript (conf={confidence:.2f}): {transcript!r}")
        return transcript.strip()
