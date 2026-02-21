"""
Standalone test for audio capture and VAD.
Run directly to verify microphone is working.
"""
import sys
import wave
sys.path.insert(0, "/home/respeaker/voice-assistant")

from audio.capture import AudioCapture

def test_list_devices():
    cap = AudioCapture()
    print("\nAvailable audio devices:")
    cap.list_devices()

def test_record_utterance():
    cap = AudioCapture()
    print("\nSpeak something after this message. Will stop after 1 second of silence.")
    audio = cap.record_utterance()
    print(f"Recorded {len(audio)} bytes ({len(audio)/32000:.1f} seconds at 16kHz mono)")

    # Save to WAV for manual inspection
    output_path = "/tmp/test_capture.wav"
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio)
    print(f"Saved to {output_path}")
    print(f"Verify with: aplay {output_path}")

if __name__ == "__main__":
    test_list_devices()
    test_record_utterance()
