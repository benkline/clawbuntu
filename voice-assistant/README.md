# ReSpeaker Core v2.0 Voice Assistant

A voice assistant running on Seeed Studio's ReSpeaker Core v2.0 with Claude AI (Anthropic), Google Cloud Speech-to-Text, and Google Cloud Text-to-Speech.

**Features:**
- Voice Activity Detection (VAD) for auto-detecting end of speech
- Conversation memory (Claude maintains context across multiple turns)
- Special commands: "reset conversation", "goodbye" to exit
- Button or keyboard trigger modes
- Configurable via `.env`

---

## Hardware Setup (Phase 1)

### 1.1 Obtain Hardware

- **ReSpeaker Core v2.0** with microSD card (8GB+ recommended)
- Power supply (micro-USB, 2A recommended)
- Optional: USB serial cable for initial setup (or use USB-OTG)

### 1.2 Flash Debian Image

1. Download the latest Debian image:
   - Visit: https://github.com/respeaker/get_started_with_respeaker/wiki
   - Download the **lxqt version** (recommended)

2. Flash to microSD using **Balena Etcher**:
   - Open Etcher
   - Select `.img.xz` file (no need to unzip)
   - Select microSD card
   - Click Flash (~10 minutes)

3. Insert microSD into ReSpeaker Core v2.0

4. Power on via micro-USB
   - LEDs will blink during eMMC flash (~10 minutes)
   - When complete, power off

5. Remove microSD, power on again
   - Device boots from eMMC
   - LEDs indicate successful boot

### 1.3 Configure Wi-Fi & SSH

1. Connect to device (serial console via USB-OTG or USB serial cable):
   ```bash
   # If using direct USB connection, you may get a serial device automatically
   # Or use: picocom /dev/ttyUSB0 -b 115200
   ```

2. Configure Wi-Fi:
   ```bash
   sudo nmtui
   # Navigate: Activate a connection > Wi-Fi
   # Select SSID, enter password
   # Wait for * to appear next to SSID
   ```

3. Get IP address:
   ```bash
   ip addr show wlan0
   # Note the IP address (e.g., 192.168.1.100)
   ```

4. SSH in from your development machine:
   ```bash
   ssh respeaker@<device-ip>
   # Default password: respeaker
   ```

5. **Change password immediately:**
   ```bash
   passwd
   ```

### 1.4 Verify Audio Hardware

```bash
# Test recording (6 mics, 8 channels total)
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav

# Test playback
aplay -D hw:0,1 /tmp/test.wav

# You should hear what you recorded through the speaker
```

### 1.5 Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    portaudio19-dev \
    libatlas-base-dev \
    ffmpeg \
    libasound-dev \
    git
```

---

## Project Setup (Phase 2)

### 2.1 Clone/Copy Project

On the ReSpeaker device:
```bash
mkdir -p /home/respeaker/voice-assistant
cd /home/respeaker/voice-assistant
# Copy files here (or git clone)
```

### 2.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# If webrtcvad fails on ARM, use webrtcvad-wheels instead:
# pip uninstall webrtcvad
# pip install webrtcvad-wheels
```

### 2.4 Configure API Keys

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
nano .env
```

**Required:**
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP JSON credentials file

**Optional:**
- `AUDIO_INPUT_DEVICE_INDEX` - Find with `python3 -c "import pyaudio; ..."`
- `TRIGGER_MODE` - "keyboard" for testing, "button" for production
- `BUTTON_GPIO_PIN` - GPIO pin for button trigger

### 2.5 GCP Setup

1. Create a GCP project and enable:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API

2. Create a service account with roles:
   - `roles/speech.client`
   - `roles/cloudtexttospeech.client`

3. Download JSON key and copy to device:
   ```bash
   scp your-key.json respeaker@<device-ip>:/home/respeaker/voice-assistant/gcp-credentials.json
   ```

4. Set in `.env`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/home/respeaker/voice-assistant/gcp-credentials.json
   ```

---

## Testing (Phase 3)

### Test 1: Audio Hardware

```bash
# Already done above, but verify again:
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav
aplay -D hw:0,1 /tmp/test.wav
```

### Test 2: PyAudio Capture

```bash
source venv/bin/activate
python3 tests/test_audio_capture.py
# Speak something, verify WAV file is created at /tmp/test_capture.wav
```

### Test 3: Google STT

```bash
python3 tests/test_stt.py /tmp/test_capture.wav
# Should print transcript of what you said
```

### Test 4: Claude Agent

```bash
python3 tests/test_claude.py
# Should pass both single-turn and memory tests
```

### Test 5: Google TTS + Playback

```bash
python3 tests/test_tts.py
# Should synthesize and play "Hello, this is a test of the voice assistant."
```

### Test 6: Full Integration

```bash
python3 main.py
# With TRIGGER_MODE=keyboard:
#   Press Enter, speak, wait for response
#   Should hear Claude's response through speaker
# Say "goodbye" to exit
```

---

## Production Setup

### Audio Device Discovery

If audio doesn't work, find the correct device indices:

```bash
python3 << 'EOF'
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    print(f"{i}: {d['name']} | in={d['maxInputChannels']} out={d['maxOutputChannels']}")
p.terminate()
EOF
```

Update `AUDIO_INPUT_DEVICE_INDEX` and `AUDIO_OUTPUT_DEVICE_INDEX` in `.env` with the correct indices.

### Button Trigger Mode

Wire a momentary push-to-talk button:
- One side → GPIO17 (default, configurable)
- Other side → GND

Update `.env`:
```
TRIGGER_MODE=button
BUTTON_GPIO_PIN=17
```

### Systemd Service (Auto-start)

Create `/etc/systemd/system/voice-assistant.service`:

```ini
[Unit]
Description=ReSpeaker Voice Assistant
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=respeaker
WorkingDirectory=/home/respeaker/voice-assistant
ExecStart=/home/respeaker/voice-assistant/venv/bin/python3 main.py
Restart=on-failure
RestartSec=5
EnvironmentFile=/home/respeaker/voice-assistant/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant
sudo journalctl -u voice-assistant -f   # Follow logs
```

---

## Troubleshooting

### No audio input
- Check device indices: `python3 tests/test_audio_capture.py`
- Verify microphone: `arecord -l`

### Google Cloud auth error
- Verify `GOOGLE_APPLICATION_CREDENTIALS` path exists
- Check service account has correct roles

### Claude API error
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API key has access to models

### Slow responses
- Switch to `claude-opus-4-6` for faster (but more expensive) responses
- Or stick with `claude-haiku-4-5-20251001` for faster latency

### Button not working
- Verify GPIO pin with: `python3 -c "import gpiozero; print(gpiozero.pi_pin_factory)"`
- Check wiring (button between GPIO + GND)
- Try keyboard trigger mode first

---

## Commands

Say these to the assistant:

- **"reset conversation"** or **"clear history"** - Clear conversation memory
- **"goodbye"** or **"quit"** - Exit gracefully

---

## Architecture

```
main.py (control loop)
  ↓
trigger (wait for user input)
  ↓
audio/capture (record with VAD)
  ↓
speech/stt (transcribe with Google STT)
  ↓
agent/claude_agent (chat with Claude)
  ↓
speech/tts (synthesize with Google TTS)
  ↓
audio/playback (play through ReSpeaker speaker)
```

All configuration flows through `config/settings.py` which loads from `.env`.

---

## Performance Notes

- **Haiku model** (default): Sub-1 second response time, suitable for voice interaction
- **Opus model**: Slower, better reasoning, use for complex queries
- **Audio latency**: ~500ms from speech end to first synthesis output
- **Total conversation loop**: ~2-3 seconds from speech end to hearing response

---

## References

- [ReSpeaker Core v2.0 Wiki](https://wiki.seeedstudio.com/ReSpeaker_Core_v2.0/)
- [ReSpeaker GitHub](https://github.com/respeaker/get_started_with_respeaker)
- [Google Cloud Speech-to-Text Docs](https://cloud.google.com/speech-to-text/docs)
- [Google Cloud Text-to-Speech Docs](https://cloud.google.com/text-to-speech/docs)
- [Anthropic Claude API](https://docs.anthropic.com/en/api/)
- [webrtcvad GitHub](https://github.com/wiseman/py-webrtcvad)
