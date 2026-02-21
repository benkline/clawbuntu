"""
Test Google Cloud TTS and playback.
"""
import sys
sys.path.insert(0, "/home/respeaker/voice-assistant")

def test_tts_synthesis():
    from speech.tts import TextToSpeech
    tts = TextToSpeech()
    audio_bytes = tts.synthesize("Hello, this is a test of the voice assistant.")
    assert len(audio_bytes) > 0, "Expected non-empty MP3 bytes"
    print(f"Got {len(audio_bytes)} bytes of MP3 audio. PASSED")
    return audio_bytes

def test_tts_playback():
    from audio.playback import AudioPlayer
    audio_bytes = test_tts_synthesis()

    player = AudioPlayer()
    print("Playing audio now...")
    player.play_mp3_bytes(audio_bytes)
    print("Playback test PASSED")

if __name__ == "__main__":
    test_tts_playback()
