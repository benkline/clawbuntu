"""
Main control loop for the ReSpeaker voice assistant.

Loop:
  1. Wait for trigger (button press or keyboard)
  2. Record audio until silence detected (VAD)
  3. Transcribe audio -> text (Google STT)
  4. Send text to Claude -> get response
  5. Synthesize response -> audio (Google TTS)
  6. Play audio through speaker
  7. Repeat

Special commands (spoken):
  "reset conversation" -> clears Claude's history
  "goodbye" / "quit"   -> exits the program
"""
import sys
import time

from config.settings import settings
from audio.capture import AudioCapture
from audio.playback import AudioPlayer
from speech.stt import SpeechToText
from speech.tts import TextToSpeech
from agent.claude_agent import ClaudeAgent
from io.trigger import get_trigger


QUIT_PHRASES = {"goodbye", "quit", "exit", "stop", "shut down"}
RESET_PHRASES = {"reset", "reset conversation", "clear history", "start over", "new conversation"}


def main():
    print("=" * 60)
    print("ReSpeaker Voice Assistant")
    print(f"Model: {settings.agent.MODEL}")
    print(f"Trigger: {settings.trigger.MODE}")
    print("=" * 60)

    # Initialize all components (fails fast if credentials missing)
    try:
        capture = AudioCapture()
        player = AudioPlayer()
        stt = SpeechToText()
        tts = TextToSpeech()
        agent = ClaudeAgent()
        trigger = get_trigger()
    except Exception as e:
        print(f"[FATAL] Failed to initialize: {e}")
        sys.exit(1)

    print("\n[Ready] Voice assistant is running.")
    print("Speak after the trigger. Say 'goodbye' to exit.\n")

    while True:
        try:
            # Step 1: Wait for user to initiate
            trigger.wait_for_trigger()

            # Step 2: Record until silence
            audio_bytes = capture.record_utterance()
            if len(audio_bytes) < 1000:
                print("[Main] Audio too short, ignoring.")
                continue

            # Step 3: Speech to Text
            transcript = stt.transcribe(audio_bytes)
            if not transcript:
                print("[Main] No transcript, looping back.")
                _speak_error(tts, player, "Sorry, I didn't catch that.")
                continue

            print(f"\n[You]: {transcript}")

            # Handle special commands
            normalized = transcript.lower().strip().rstrip(".")
            if normalized in QUIT_PHRASES:
                farewell_audio = tts.synthesize("Goodbye!")
                player.play_mp3_bytes(farewell_audio)
                print("[Main] Exiting.")
                break

            if normalized in RESET_PHRASES:
                agent.reset_history()
                reset_audio = tts.synthesize("Conversation reset. How can I help you?")
                player.play_mp3_bytes(reset_audio)
                continue

            # Step 4: Claude agent
            response_text = agent.chat(transcript)
            print(f"\n[Claude]: {response_text}\n")

            # Step 5 + 6: TTS and playback
            audio_response = tts.synthesize(response_text)
            player.play_mp3_bytes(audio_response)

        except KeyboardInterrupt:
            print("\n[Main] Keyboard interrupt received. Shutting down.")
            break
        except Exception as e:
            print(f"[Main] Error in main loop: {e}")
            # Don't crash the loop on transient errors
            time.sleep(1)
            continue

    print("[Main] Shutdown complete.")


def _speak_error(tts: TextToSpeech, player: AudioPlayer, message: str):
    """Utility to speak an error message without crashing."""
    try:
        audio = tts.synthesize(message)
        player.play_mp3_bytes(audio)
    except Exception:
        pass  # Best-effort; don't recurse on error


if __name__ == "__main__":
    main()
