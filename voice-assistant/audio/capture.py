"""
Audio capture module with Voice Activity Detection.

Flow:
  1. Open PyAudio stream on the ReSpeaker input device
  2. Collect audio in fixed 30ms frames
  3. Feed each frame to webrtcvad
  4. State machine transitions:
       WAITING  -> RECORDING when speech detected
       RECORDING -> DONE when N consecutive silent frames seen
  5. Return raw PCM bytes of the entire utterance

webrtcvad constraints:
  - Only supports 8000, 16000, 32000, 48000 Hz
  - Frame duration must be exactly 10, 20, or 30 ms
  - Audio must be 16-bit signed PCM mono
"""
import pyaudio
import webrtcvad
import collections
from config.settings import settings


class AudioCapture:
    def __init__(self):
        cfg = settings.audio
        self.sample_rate = cfg.SAMPLE_RATE
        self.channels = cfg.CHANNELS
        self.sample_width = cfg.SAMPLE_WIDTH
        self.input_device_index = cfg.INPUT_DEVICE_INDEX
        self.frame_duration_ms = cfg.VAD_FRAME_MS

        # Bytes per frame: rate * (ms/1000) * bytes_per_sample * channels
        self.frame_bytes = int(
            self.sample_rate * self.frame_duration_ms / 1000
        ) * self.sample_width * self.channels

        self.silence_threshold = cfg.SILENCE_FRAMES_THRESHOLD
        self.vad_aggressiveness = cfg.VAD_AGGRESSIVENESS

        self._pa = pyaudio.PyAudio()
        self._vad = webrtcvad.Vad(self.vad_aggressiveness)

    def _open_stream(self):
        return self._pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.frame_bytes // self.sample_width,
        )

    def record_utterance(self, pre_speech_frames: int = 10) -> bytes:
        """
        Block until a complete utterance is captured.

        Records audio starting slightly before speech is detected
        (using a ring buffer of pre_speech_frames) and stops after
        SILENCE_FRAMES_THRESHOLD consecutive silent frames.

        Returns:
            Raw 16-bit mono PCM bytes at SAMPLE_RATE Hz.
        """
        stream = self._open_stream()
        ring_buffer = collections.deque(maxlen=pre_speech_frames)
        triggered = False
        voiced_frames = []
        silent_frame_count = 0

        print("[Capture] Listening for speech...")
        try:
            while True:
                frame = stream.read(
                    self.frame_bytes // self.sample_width,
                    exception_on_overflow=False,
                )

                is_speech = self._vad.is_speech(frame, self.sample_rate)

                if not triggered:
                    ring_buffer.append(frame)
                    if is_speech:
                        triggered = True
                        print("[Capture] Speech detected, recording...")
                        # Include the pre-speech buffer so we don't clip the start
                        voiced_frames.extend(list(ring_buffer))
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    if not is_speech:
                        silent_frame_count += 1
                        if silent_frame_count >= self.silence_threshold:
                            print(
                                f"[Capture] Silence detected after "
                                f"{len(voiced_frames)} frames. Done."
                            )
                            break
                    else:
                        silent_frame_count = 0
        finally:
            stream.stop_stream()
            stream.close()

        return b"".join(voiced_frames)

    def list_devices(self):
        """Utility: print all audio devices for finding the correct index."""
        count = self._pa.get_device_count()
        for i in range(count):
            info = self._pa.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                print(f"  Input  device {i}: {info['name']}")
            if info.get("maxOutputChannels", 0) > 0:
                print(f"  Output device {i}: {info['name']}")

    def __del__(self):
        if self._pa:
            self._pa.terminate()
