"""
Audio playback module.

Google TTS returns MP3 bytes. We use pydub to decode MP3 in-memory,
then play via PyAudio to the correct output device.

pydub requires ffmpeg to be installed for MP3 decoding.
"""
import io
import pyaudio
import wave
from pydub import AudioSegment
from config.settings import settings


class AudioPlayer:
    def __init__(self):
        self.output_device_index = settings.audio.OUTPUT_DEVICE_INDEX
        self._pa = pyaudio.PyAudio()

    def play_mp3_bytes(self, mp3_bytes: bytes) -> None:
        """
        Decode MP3 bytes and play through the ReSpeaker speaker output.
        Blocks until playback is complete.
        """
        # Decode MP3 -> raw PCM using pydub (requires ffmpeg)
        audio_segment = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))

        # Normalize to mono 16-bit PCM at the system sample rate
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_sample_width(2)  # 16-bit
        audio_segment = audio_segment.set_frame_rate(22050)  # TTS native rate

        raw_pcm = audio_segment.raw_data
        sample_rate = audio_segment.frame_rate
        channels = audio_segment.channels
        sample_width = audio_segment.sample_width

        stream = self._pa.open(
            format=self._pa.get_format_from_width(sample_width),
            channels=channels,
            rate=sample_rate,
            output=True,
            output_device_index=self.output_device_index,
        )

        # Write in chunks to avoid buffer overruns
        chunk_size = 1024
        for i in range(0, len(raw_pcm), chunk_size):
            stream.write(raw_pcm[i : i + chunk_size])

        stream.stop_stream()
        stream.close()
        print("[Playback] Done.")

    def play_wav_bytes(self, wav_bytes: bytes) -> None:
        """Alternative: play raw WAV bytes (useful for LINEAR16 TTS output)."""
        wav_io = io.BytesIO(wav_bytes)
        with wave.open(wav_io, "rb") as wf:
            stream = self._pa.open(
                format=self._pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.output_device_index,
            )
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            stream.stop_stream()
            stream.close()

    def __del__(self):
        if self._pa:
            self._pa.terminate()
