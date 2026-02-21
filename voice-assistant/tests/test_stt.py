"""
Test Google Cloud STT with a pre-recorded WAV file or live recording.
"""
import sys
import wave
sys.path.insert(0, "/home/respeaker/voice-assistant")

def test_stt_with_wav(wav_path: str):
    with wave.open(wav_path, "rb") as wf:
        audio_bytes = wf.readframes(wf.getnframes())

    from speech.stt import SpeechToText
    stt = SpeechToText()
    transcript = stt.transcribe(audio_bytes)
    print(f"Transcript: {transcript!r}")
    assert transcript, "Expected non-empty transcript"
    print("STT test PASSED")

def test_stt_live():
    from audio.capture import AudioCapture
    from speech.stt import SpeechToText

    cap = AudioCapture()
    stt = SpeechToText()

    print("Speak something now...")
    audio = cap.record_utterance()
    transcript = stt.transcribe(audio)
    print(f"Transcript: {transcript!r}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_stt_with_wav(sys.argv[1])
    else:
        test_stt_live()
