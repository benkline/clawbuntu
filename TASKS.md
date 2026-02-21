# Task Execution Guide - ReSpeaker Voice Assistant

This guide walks you through all 4 tasks to get your voice assistant up and running.

---

## Task #1: Prepare ReSpeaker Core v2.0 Hardware and OS

**Goal:** Get the physical device running Debian with Wi-Fi and SSH access.

### Step 1.1: Obtain Hardware
- [ ] ReSpeaker Core v2.0 device
- [ ] MicroSD card (8GB or larger)
- [ ] Micro-USB power cable (2A recommended)
- [ ] Optional: USB serial cable for debugging

### Step 1.2: Download and Flash Debian Image

1. Visit: https://github.com/respeaker/get_started_with_respeaker/wiki
2. Download the **lxqt version** image (recommended)
3. Install **Balena Etcher**: https://www.balena.io/etcher/
4. Open Etcher and:
   - [ ] Select the `.img.xz` file (no need to unzip)
   - [ ] Select your microSD card
   - [ ] Click "Flash" (takes ~10 minutes)
5. When complete, eject the microSD card

### Step 1.3: Initial Boot and LED Check

1. [ ] Insert microSD into ReSpeaker Core v2.0
2. [ ] Power on via micro-USB cable
3. Watch the LEDs:
   - They will **blink alternately** during eMMC flash (~10 minutes)
   - When flash completes, **LEDs go dark**
4. [ ] Power off device
5. [ ] Remove microSD card
6. [ ] Power on again
   - Device boots from eMMC
   - LEDs light up = success

### Step 1.4: Configure Wi-Fi via Serial Console

You need initial access to the device. Choose one method:

**Option A: Direct USB Connection (easiest)**
- Connect ReSpeaker to your Mac via USB-A to USB-C cable
- A serial device may appear automatically

**Option B: USB Serial Cable**
- Use a USB-to-serial adapter connected to UART pins
- Connect at 115200 baud

Once you have console access:

```bash
# Configure Wi-Fi
sudo nmtui

# Navigate:
# 1. Select "Activate a connection"
# 2. Select "Wi-Fi"
# 3. Choose your SSID
# 4. Enter password
# 5. Wait for * to appear (indicates connection)
```

### Step 1.5: Get Device IP Address

```bash
ip addr show wlan0
# Look for "inet 192.168.x.x" or similar
# Example: 192.168.1.100
# Note this IP address
```

### Step 1.6: SSH Access and Password Change

From your development machine (Mac):

```bash
# SSH into the device
ssh respeaker@<device-ip>
# Example: ssh respeaker@192.168.1.100
# Password: respeaker

# IMMEDIATELY change the password
passwd
# Follow the prompts to set a new password
```

**Verification:**
- [ ] Can SSH into device without entering password (if you set up key auth)
- [ ] Or can SSH with new password

### Step 1.7: Verify Audio Hardware

SSH into the device and test:

```bash
# Test recording from microphones
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav

# Test playback through speaker
aplay -D hw:0,1 /tmp/test.wav
```

**Verification:**
- [ ] `arecord` captures 5 seconds of audio to file
- [ ] `aplay` plays it back through the speaker
- [ ] You can hear yourself!

### Step 1.8: Install System Dependencies

SSH into device and run:

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

**Verification:**
- [ ] All packages installed without errors
- [ ] Run: `python3 --version` → shows 3.x
- [ ] Run: `ffmpeg -version` → shows FFmpeg info

### Step 1.9: Create Project Directory

```bash
ssh respeaker@<device-ip>

# Create project directory
mkdir -p /home/respeaker/voice-assistant
cd /home/respeaker/voice-assistant

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Verify venv is active (should see (venv) in prompt)
```

**Verification:**
- [ ] Can SSH into `/home/respeaker/voice-assistant`
- [ ] Virtual environment activated (`(venv)` appears in terminal)

### ✅ Task #1 Complete When:
- [x] Device boots into Debian
- [x] Wi-Fi configured and connected
- [x] Can SSH into device
- [x] Audio hardware verified (arecord/aplay works)
- [x] System dependencies installed
- [x] Python venv created

**Next:** Move to Task #2

---

## Task #2: Deploy Code to ReSpeaker and Configure Environment

**Goal:** Get the voice-assistant code running on the device with all credentials configured.

### Step 2.1: Copy Project Files to Device

From your **Mac** (in the project directory):

```bash
# Navigate to project directory
cd /Users/benkline/Projects/clawbuntu

# Copy the voice-assistant folder to the device
scp -r voice-assistant/* respeaker@<device-ip>:/home/respeaker/voice-assistant/

# Verify files copied
ssh respeaker@<device-ip> ls -la /home/respeaker/voice-assistant/
# Should show: config, audio, speech, agent, io, tests, main.py, requirements.txt, etc.
```

### Step 2.2: Install Python Dependencies

SSH into device:

```bash
ssh respeaker@<device-ip>
cd /home/respeaker/voice-assistant
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# If webrtcvad fails on ARM, use this instead:
# pip uninstall webrtcvad
# pip install webrtcvad-wheels
```

**Verification:**
- [ ] All packages install successfully
- [ ] No error messages
- [ ] Can import: `python3 -c "import pyaudio; print('OK')"`

### Step 2.3: Get Google Cloud Credentials

**On your Mac:**

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing):
   - [ ] Project name: `respeaker-assistant` (or your choice)
3. Enable APIs:
   - [ ] Go to APIs & Services → Library
   - [ ] Search "Speech-to-Text" → Enable
   - [ ] Search "Text-to-Speech" → Enable
4. Create service account:
   - [ ] APIs & Services → Credentials → Create Credentials → Service Account
   - [ ] Name: `respeaker-voice`
   - [ ] Click Create
5. Grant roles to service account:
   - [ ] On the service account, click it to open details
   - [ ] Go to IAM & Admin → Roles
   - [ ] Grant roles:
     - [ ] `roles/speech.client`
     - [ ] `roles/cloudtexttospeech.client`
6. Create and download JSON key:
   - [ ] In service account details, go to "Keys"
   - [ ] Create new key → JSON
   - [ ] Save file (e.g., `gcp-key.json`)

### Step 2.4: Copy GCP Credentials to Device

From your **Mac**:

```bash
# Copy the GCP JSON key to the device
scp ~/Downloads/gcp-key.json respeaker@<device-ip>:/home/respeaker/voice-assistant/gcp-credentials.json

# Verify
ssh respeaker@<device-ip> ls -la /home/respeaker/voice-assistant/gcp-credentials.json
```

### Step 2.5: Get Anthropic API Key

1. Go to https://console.anthropic.com/api/keys
2. Sign in with your Anthropic account (create one if needed)
3. [ ] Create a new API key
4. [ ] Copy the key (starts with `sk-ant-`)
5. Keep it somewhere safe (you'll need it next)

### Step 2.6: Create .env File on Device

SSH into device:

```bash
cd /home/respeaker/voice-assistant

# Copy template
cp .env.example .env

# Edit the .env file
nano .env
```

You'll see the template. Edit these key lines:

```ini
# Replace with the actual path (should already be correct)
GOOGLE_APPLICATION_CREDENTIALS=/home/respeaker/voice-assistant/gcp-credentials.json

# Replace with your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-... (your actual key here)

# For initial testing, keep these as-is:
TRIGGER_MODE=keyboard
AUDIO_INPUT_DEVICE_INDEX=0
AUDIO_OUTPUT_DEVICE_INDEX=0
CLAUDE_MODEL=claude-haiku-4-5-20251001
```

**Save the file:**
- [ ] Press `Ctrl+X`
- [ ] Press `Y` to confirm save
- [ ] Press `Enter` to keep filename

### Step 2.7: Discover Audio Device Indices

SSH into device and run:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

python3 << 'EOF'
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    print(f"{i}: {d['name']} | in={d['maxInputChannels']} out={d['maxOutputChannels']}")
p.terminate()
EOF
```

Look for `seeed` in the device name. Note the index number.

**Update .env if needed:**
```bash
nano .env
# Change AUDIO_INPUT_DEVICE_INDEX and AUDIO_OUTPUT_DEVICE_INDEX to the correct indices
```

### Step 2.8: Verify Credentials Work

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

# Test Google Cloud auth
python3 -c "from google.cloud import speech; c = speech.SpeechClient(); print('Google auth OK')"

# Test Anthropic auth
python3 -c "import anthropic; c = anthropic.Anthropic(); print('Anthropic auth OK')"
```

**Verification:**
- [ ] Both commands print "OK"
- [ ] No authentication errors

### ✅ Task #2 Complete When:
- [x] Code files copied to device
- [x] Python dependencies installed
- [x] GCP credentials downloaded and copied
- [x] Anthropic API key obtained
- [x] .env file configured with credentials
- [x] Audio device indices verified
- [x] Google and Anthropic auth tests pass

**Next:** Move to Task #3

---

## Task #3: Run Component Tests and Validate Full Integration

**Goal:** Verify each component works individually, then test the full pipeline.

### Step 3.1: Test Audio Hardware (ALSA Level)

SSH into device:

```bash
# Test recording
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test_hw.wav

# Test playback
aplay -D hw:0,1 /tmp/test_hw.wav
```

**Verification:**
- [ ] Recording completes without errors
- [ ] You hear your own voice played back

### Step 3.2: Test Audio Capture with VAD

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

python3 tests/test_audio_capture.py
```

**What to do:**
- The script will show a list of audio devices
- Then prompt: "Speak something after this message. Will stop after 1 second of silence."
- [ ] Speak clearly into the microphone
- [ ] Wait for 1 second of silence
- [ ] Script saves to `/tmp/test_capture.wav`

**Verification:**
- [ ] Script runs without crashing
- [ ] File created: `aplay -D hw:0,1 /tmp/test_capture.wav`
- [ ] You hear what you said recorded

### Step 3.3: Test Google STT (Speech-to-Text)

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

# Use the WAV file from Step 3.2
python3 tests/test_stt.py /tmp/test_capture.wav
```

**Verification:**
- [ ] Prints transcript of what you said
- [ ] Confidence score shown (0.0-1.0)
- [ ] No API errors

**If it fails:**
- Check `GOOGLE_APPLICATION_CREDENTIALS` path
- Verify JSON credentials file exists
- Check GCP service account has `roles/speech.client` role

### Step 3.4: Test Claude Agent

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

python3 tests/test_claude.py
```

**What happens:**
- Test 1: Asks "What is the capital of France?" → checks for "Paris" in response
- Test 2: Says "My name is Alex." then "What is my name?" → checks memory

**Verification:**
- [ ] Both tests print "PASSED"
- [ ] Response includes "Paris"
- [ ] Response remembers "Alex"

**If it fails:**
- Check `ANTHROPIC_API_KEY` is correct
- Verify API key has access to claude models
- Check rate limits aren't exceeded

### Step 3.5: Test Google TTS (Text-to-Speech) + Playback

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

python3 tests/test_tts.py
```

**What happens:**
- Synthesizes: "Hello, this is a test of the voice assistant."
- Decodes MP3 audio
- Plays through ReSpeaker speaker

**Verification:**
- [ ] Prints "Got X bytes of MP3 audio. PASSED"
- [ ] You hear the sentence through the speaker

**If it fails:**
- Check `GOOGLE_APPLICATION_CREDENTIALS` path
- Verify ffmpeg is installed: `ffmpeg -version`
- Check audio playback device index is correct

### Step 3.6: Full Integration Test

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

python3 main.py
```

**What to do:**
1. Script starts and shows:
   ```
   ============================================================
   ReSpeaker Voice Assistant
   Model: claude-haiku-4-5-20251001
   Trigger: keyboard
   ============================================================

   [Ready] Voice assistant is running.
   Speak after the trigger. Say 'goodbye' to exit.
   ```

2. [ ] Press **Enter** (keyboard trigger)
3. [ ] Speak a question: "What is the weather like?" or "Tell me a joke"
4. [ ] Wait for 1 second of silence (VAD detection)
5. [ ] You should hear Claude's response through the speaker
6. [ ] Press **Enter** again for another turn
7. [ ] Say "goodbye" to exit

**Expected output:**
```
[Trigger] Press ENTER to speak (or Ctrl+C to quit)...

[Capture] Listening for speech...
[Capture] Speech detected, recording...
[Capture] Silence detected after XX frames. Done.

[STT] Sending XXXX bytes to Google STT...
[STT] Transcript (conf=0.XX): "what is the weather like?"

[You]: what is the weather like?

[Agent] Sending to Claude (claude-haiku-4-5-20251001), history=1 messages...
[Agent] Response: I don't have real-time weather data, but you can check...

[Claude]: I don't have real-time weather data, but you can check...

[TTS] Synthesizing: I don't have real-time weather data, but you can check...
[TTS] Received XXXX bytes of MP3 audio.
[Playback] Done.
```

**Verification:**
- [ ] Full loop completes successfully
- [ ] You hear the response
- [ ] No errors in the output
- [ ] Exit with "goodbye" works

### Troubleshooting Full Integration

| Issue | Solution |
|-------|----------|
| "No audio input" | Check device indices in .env |
| "Google auth failed" | Verify gcp-credentials.json exists and path is correct |
| "Anthropic auth failed" | Verify ANTHROPIC_API_KEY is correct in .env |
| "No speech recognized" | Speak louder/clearer, adjust VAD_AGGRESSIVENESS in .env |
| "Response is slow" | Normal for first run. Claude Haiku takes ~500ms per request |
| "Audio playback cuts off" | Reduce response token size: `CLAUDE_MAX_TOKENS=256` |

### ✅ Task #3 Complete When:
- [x] Hardware audio test passes
- [x] Audio capture with VAD test passes
- [x] Google STT test passes
- [x] Claude agent test passes (both single and multi-turn)
- [x] Google TTS + playback test passes
- [x] Full integration loop works end-to-end
- [x] Can have multiple conversation turns
- [x] Can exit gracefully with "goodbye"

**Next:** Move to Task #4

---

## Task #4: Set up Button Trigger and Systemd Auto-Start Service

**Goal:** Enable production setup with GPIO button and auto-start on boot.

### Part A: GPIO Button Trigger (Optional but Recommended)

#### Step 4A.1: Wire the Button

The ReSpeaker Core v2.0 has a 40-pin GPIO header. Wire a momentary push-to-talk button:

- One side of button → **GPIO17** (configurable)
- Other side of button → **GND** (ground)

Pin locations on header:
- GPIO17: Pin 11
- GND: Pin 6 or 9 or 14 or 20 or 25 or 30 or 34 or 39

Reference: https://wiki.seeedstudio.com/ReSpeaker_Core_v2.0/ (see pinout diagram)

**Verification:**
- [ ] Button wired correctly
- [ ] No loose connections

#### Step 4A.2: Update .env for Button Mode

SSH into device:

```bash
cd /home/respeaker/voice-assistant

nano .env
```

Change these lines:

```ini
TRIGGER_MODE=button
BUTTON_GPIO_PIN=17
```

Save: `Ctrl+X` → `Y` → `Enter`

#### Step 4A.3: Test Button Trigger

SSH into device:

```bash
cd /home/respeaker/voice-assistant
source venv/bin/activate

python3 main.py
```

**What to do:**
1. Script should print:
   ```
   [Trigger] Waiting for button press on GPIO 17...
   ```

2. [ ] **Press the physical button** (momentary push-to-talk)
3. [ ] Script prints: `[Trigger] Button pressed.`
4. [ ] [ ] Speak your question
5. [ ] [ ] Wait for response
6. [ ] [ ] Press button again for another turn
7. [ ] [ ] Say "goodbye" to exit

**Verification:**
- [ ] Button press is detected
- [ ] Full conversation loop works with button
- [ ] No errors in output

**Troubleshooting:**
- If button not detected:
  - Verify wiring (button between GPIO17 and GND)
  - Try keyboard mode first to ensure everything else works
  - Check GPIO pin with: `cat /sys/class/gpio/gpio17/value` (should be 1, becomes 0 when pressed)

---

### Part B: Systemd Auto-Start Service

#### Step 4B.1: Create Systemd Service File

SSH into device and create the service file:

```bash
sudo nano /etc/systemd/system/voice-assistant.service
```

Paste the following:

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

Save: `Ctrl+X` → `Y` → `Enter`

#### Step 4B.2: Enable and Start Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable voice-assistant

# Start the service now
sudo systemctl start voice-assistant
```

#### Step 4B.3: Verify Service is Running

```bash
# Check status
sudo systemctl status voice-assistant

# Follow the logs in real-time
sudo journalctl -u voice-assistant -f
```

Expected output:
```
● voice-assistant.service - ReSpeaker Voice Assistant
     Loaded: loaded (/etc/systemd/system/voice-assistant.service; enabled; vendor preset: enabled)
     Active: active (running) since ...
```

**Verification:**
- [ ] Status shows "active (running)"
- [ ] Logs show no errors
- [ ] Service can be controlled:
  ```bash
  sudo systemctl restart voice-assistant
  sudo systemctl stop voice-assistant
  ```

#### Step 4B.4: Test Auto-Start on Reboot

```bash
# Reboot the device
sudo reboot

# Wait ~30 seconds for device to boot
# SSH back in
ssh respeaker@<device-ip>

# Check if service is running
sudo systemctl status voice-assistant

# Check logs
sudo journalctl -u voice-assistant -n 20
```

**Expected behavior:**
- Service automatically starts after boot
- Voice assistant is ready to use
- Logs show clean startup with no errors

**Verification:**
- [ ] Service status is "active (running)"
- [ ] No error messages in logs
- [ ] Press button (or Enter if keyboard mode) and assistant responds

#### Step 4B.5: Disable Service (if needed)

If you need to stop the service from auto-starting:

```bash
sudo systemctl stop voice-assistant
sudo systemctl disable voice-assistant
```

---

### Advanced: View and Manage Service Logs

```bash
# View last 50 log lines
sudo journalctl -u voice-assistant -n 50

# Follow logs live
sudo journalctl -u voice-assistant -f

# View logs since service started
sudo journalctl -u voice-assistant --since "1 hour ago"

# View only errors
sudo journalctl -u voice-assistant -p err
```

---

### ✅ Task #4 Complete When:
- [x] GPIO button wired and working (if doing button mode)
- [x] .env updated for button trigger
- [x] Button trigger tested in main.py
- [x] Systemd service file created
- [x] Service enabled and started
- [x] Service status shows "active (running)"
- [x] Auto-start verified after reboot
- [x] Voice assistant works with button trigger after reboot

---

## 🎉 All Tasks Complete!

Your voice assistant is now:
- ✅ Running on ReSpeaker Core v2.0
- ✅ Responding to voice commands
- ✅ Maintaining conversation memory with Claude
- ✅ Auto-starting after device reboot
- ✅ Ready for production use!

### Next Steps (Optional Enhancements)

1. **Change AI Model:** Edit `.env` to use `claude-opus-4-6` for better reasoning (slower/more expensive)
2. **Adjust Voice:** Try different `TTS_VOICE_NAME` values (see README.md)
3. **Tune Audio:** Adjust `VAD_AGGRESSIVENESS` and `SILENCE_FRAMES_THRESHOLD` for your environment
4. **Monitor Logs:** Use `journalctl` to monitor the service
5. **Push Updates:** Make changes locally, commit to GitHub, then pull on device

### GitHub Repository
All code is tracked at: https://github.com/benkline/clawbuntu

### Support Resources
- Full documentation: `voice-assistant/README.md`
- Quick start: `QUICKSTART.md`
- Plan details: `.claude/plans/fluffy-percolating-cloud.md`

---

**Good luck with your voice assistant! 🚀**
