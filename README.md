# Speech-to-Text App

A simple global speech-to-text application that records audio on hotkey press and types the transcribed text into the active window.

## What it does

- Hold F1 to record audio
- Release F1 to transcribe with OpenAI Whisper and type the result
- Uses FFmpeg to remove silence, normalize audio, and speed up 2x (reduces costs by 60-90%)
- 3 minute maximum recording length
- Runs in background, works system-wide

## Installation 
- Install ffmpeg using your package manager

### Arch Linux

#### Install dependencies

```bash
# NOTE: Some of these might only be available via AUR
sudo pacman -S python-pyaudio python-openai python-pynput ffmpeg
```

### Setup
1. Clone or download this repository
2. Set your OpenAI API key:
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```
3. Install autostart:

> ![IMPORTANT]
> This will only run correctly if it has access to your OpenAI key somehow.

```bash
./install.sh
```


## Usage

### Manual start
```bash
python3 silence_optimized_stt.py
```

### Controls
- **F1**: Hold to record, release to transcribe and type
- **ESC**: Exit application

## Files

- `silence_optimized_stt.py` - **Recommended** - FFmpeg silence removal + normalization + 2x speed
- `install.sh` - Sets up autostart on login

## Cost Optimization

The script uses FFmpeg post-processing to:
- Remove silence from beginning, end, and reduce gaps between speech
- Normalize audio volume for better transcription of quiet speech
- Speed up audio 2x before sending to OpenAI Whisper API

Since OpenAI charges by duration ($0.006/minute), this can reduce costs by 60-90% depending on how much silence is removed, while preserving transcription accuracy.
