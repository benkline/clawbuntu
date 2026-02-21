# Voice Assistant Quick Start Guide

**Project Location:** `/Users/benkline/Projects/clawbuntu/voice-assistant/`

## What's Been Created

A complete ReSpeaker Core v2.0 voice assistant with:
- **Speech-to-Text**: Google Cloud Speech-to-Text API
- **AI Agent**: Anthropic Claude (Haiku by default, configurable)
- **Text-to-Speech**: Google Cloud Text-to-Speech API
- **Voice Activity Detection**: Automatic end-of-speech detection
- **Conversation Memory**: Claude remembers context across turns
- **Flexible Input**: Keyboard trigger (dev) or GPIO button trigger (production)

## Project Structure

```
voice-assistant/
├── config/settings.py          # All configuration (loads from .env)
├── audio/
│   ├── capture.py              # PyAudio + webrtcvad VAD state machine
│   └── playback.py             # pydub MP3 decode + PyAudio output
├── speech/
│   ├── stt.py                  # Google Cloud STT
│   └── tts.py                  # Google Cloud TTS
├── agent/
│   └── claude_agent.py         # Claude with conversation history
├── io/
│   └── trigger.py              # Keyboard or GPIO button trigger
├── tests/                      # Component tests
├── main.py                     # Main control loop
├── requirements.txt            # Python dependencies
├── .env.example               # Config template
├── README.md                   # Full documentation
└── .gitignore
```

## Next Steps (in order)

### Step 1: Prepare Hardware (Task #1)
Before you can test anything, you need the ReSpeaker Core v2.0 set up:

1. Get the ReSpeaker Core v2.0 device
2. Download Debian image from: https://wiki.seeedstudio.com/ReSpeaker_Core_v2.0/
3. Flash to microSD using Balena Etcher
4. Boot device, configure Wi-Fi, SSH in
5. Verify audio hardware works with `arecord` / `aplay`

**Status:** See Task #1 in your task list

### Step 2: Deploy Code (Task #2)
Once hardware is ready:

1. Copy `voice-assistant/` folder to device at `/home/respeaker/voice-assistant/`
2. Create Python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Get API keys:
   - **Anthropic**: https://console.anthropic.com/api/keys
   - **Google Cloud**: Create service account with Speech-to-Text and Text-to-Speech access
5. Create `.env` file with credentials

**Critical Environment Variables:**
```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=/home/respeaker/voice-assistant/gcp-credentials.json
TRIGGER_MODE=keyboard  # For initial testing
```

### Step 3: Test Components (Task #3)
Run tests in this order:

```bash
# Test 1: Audio hardware
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav
aplay -D hw:0,1 /tmp/test.wav

# Test 2: Audio capture with VAD
python3 tests/test_audio_capture.py

# Test 3: Google STT
python3 tests/test_stt.py /tmp/test_capture.wav

# Test 4: Claude agent
python3 tests/test_claude.py

# Test 5: Google TTS + playback
python3 tests/test_tts.py

# Test 6: Full integration
python3 main.py
```

### Step 4: Production Setup (Task #4)
Once everything works:

1. **Add button trigger:**
   - Wire push-to-talk button to GPIO17 + GND
   - Change `.env`: `TRIGGER_MODE=button`

2. **Enable auto-start:**
   - Create systemd service (see README.md for details)
   - Service auto-restarts on failure and after reboot

## Key Features

### Special Voice Commands
- **"reset conversation"** or **"clear history"** → Clears conversation memory
- **"goodbye"** or **"quit"** → Gracefully exits

### Configuration Options
Edit `.env` to customize:

```ini
# Model choice
CLAUDE_MODEL=claude-haiku-4-5-20251001  # Fast, cheap
CLAUDE_MODEL=claude-opus-4-6             # Slow, expensive, better reasoning

# Voice characteristics
TTS_VOICE_NAME=en-US-Neural2-J           # Male voice
TTS_VOICE_NAME=en-US-Neural2-F           # Female voice
TTS_SPEAKING_RATE=1.0                    # 0.25 to 4.0

# Audio sensitivity
VAD_AGGRESSIVENESS=2                     # 1-3 (3 = more aggressive noise filtering)
SILENCE_FRAMES_THRESHOLD=33              # ~1 second of silence (higher = more patient)

# Memory
MAX_HISTORY_TURNS=10                     # Number of conversation turns to remember
```

## API Costs (Estimate)

**Per 1-minute conversation:**
- Google STT: ~$0.002
- Google TTS: ~$0.0001
- Claude Haiku: ~$0.0001
- **Total: ~$0.0021 per minute**

Roughly $1.25 per 600 minutes of continuous conversation.

## Troubleshooting

### Audio issues
- Check device indices: `python3 -c "import pyaudio; p=pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)) for i in range(p.get_device_count())]"`
- Verify ALSA: `arecord -l` and `aplay -l`

### API issues
- Verify credentials are in place and environment variables are set
- Check GCP service account has the right roles
- Verify Anthropic API key is valid

### Slow responses
- Switch from Haiku to Opus in `.env` (slower but better reasoning)
- Or accept slower response time as normal for voice interaction

### Button not working
- Check GPIO pin wiring
- Try keyboard mode first to verify everything else works
- Use `gpiozero` to test GPIO directly

## Architecture Overview

```
┌─────────────────────────────────────────┐
│      main.py (control loop)             │
│  Orchestrates the full voice pipeline   │
└────────────┬────────────────────────────┘
             │
       ┌─────┴──────┐
       │             │
    ┌──▼──┐    ┌────▼────┐
    │Trigger     Configuration
    │(Button)   (settings.py)
    │(Keyboard) │
    └──┬──┘    └────┬────┘
       │            │
    ┌──▼────────────▼───┐
    │  Audio Capture    │
    │  (VAD detection)  │
    └────────┬──────────┘
             │
        ┌────▼────┐
        │   STT   │ Google Cloud Speech-to-Text
        └────┬────┘
             │
        ┌────▼────┐
        │ Claude  │ Anthropic AI Agent
        │ Agent   │
        └────┬────┘
             │
        ┌────▼────┐
        │   TTS   │ Google Cloud Text-to-Speech
        └────┬────┘
             │
        ┌────▼────────┐
        │Audio Playback│
        │(Speaker)     │
        └──────────────┘
```

## Performance Notes

- **End-to-end latency**: ~2-3 seconds from speech end to hearing response
- **Model response time**: ~500ms (Haiku), ~2s (Opus)
- **Audio processing**: ~500ms capture + VAD + STT
- **Optimal for**: Conversational interaction, voice commands, simple Q&A

## Next: Read README.md

For detailed setup instructions, troubleshooting, and API configuration, see `voice-assistant/README.md`.

---

**Questions?** Check the full plan at `/Users/benkline/.claude/plans/fluffy-percolating-cloud.md`
