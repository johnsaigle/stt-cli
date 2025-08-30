#!/usr/bin/env python3
"""
Silence-Optimized Speech-to-Text
- Record naturally without auto-stopping
- FFmpeg removes silence and normalizes audio after recording
- Speed up processed audio for cost savings
"""

import os
import pyaudio
import wave
import tempfile
import threading
import time
import subprocess
from pathlib import Path
from openai import OpenAI
import pynput.keyboard as keyboard

# Suppress ALSA warnings
os.environ['ALSA_PCM_CARD'] = 'default'
os.environ['ALSA_PCM_DEVICE'] = '0'

class SilenceOptimizedSpeechToText:
    def __init__(self):
        # Get API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Set OPENAI_API_KEY environment variable")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Audio settings
        self.sample_rate = 16000  # Good for Whisper
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        
        # Recording settings
        self.max_recording_seconds = 180  # 3 minutes
        
        # State
        self.is_recording = False
        self.audio_frames = []
        self.recording_start_time = None
        
        # Keyboard controller
        self.keyboard = keyboard.Controller()
        
        print("Speech-to-Text with Silence Removal & Audio Optimization")
        print("Hold F1 to record (up to 3min) -> FFmpeg processes -> Transcribe -> Type")
        print("Press ESC to exit")

    def record_audio(self):
        """Record audio naturally without interruption"""
        self.audio_frames = []
        self.recording_start_time = time.time()
        
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("Recording... (speak naturally)")
            
            while self.is_recording:
                elapsed = time.time() - self.recording_start_time
                
                # Check 3-minute limit
                if elapsed > self.max_recording_seconds:
                    print(f"Max recording time ({self.max_recording_seconds//60}min) reached")
                    break
                
                # Progress indicator every 15 seconds
                if int(elapsed) % 15 == 0 and elapsed > 0 and int(elapsed) != int(elapsed - 1):
                    print(f"Recording... {int(elapsed)}s")
                
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.audio_frames.append(data)
                except Exception as e:
                    print(f"Recording error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"Recording failed: {e}")
        finally:
            self.is_recording = False

    def process_audio_with_ffmpeg(self, input_path, output_path):
        """Use FFmpeg to remove silence, normalize, and speed up audio"""
        try:
            # FFmpeg pipeline: remove silence, normalize, speed up
            cmd = [
                'ffmpeg', '-i', input_path,
                '-af', 
                'silenceremove=start_periods=1:start_duration=0.1:start_threshold=-60dB:stop_periods=1:stop_duration=0.3:stop_threshold=-60dB,'
                'dynaudnorm=p=0.9:g=5:r=0.9,'
                'atempo=2.0',
                '-ar', str(self.sample_rate),
                '-ac', str(self.channels),
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg processing failed: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Audio processing error: {e}")
            return False

    def get_audio_duration(self, audio_path):
        """Get duration of audio file using FFmpeg"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
                   '-of', 'csv=p=0', audio_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return 0

    def transcribe_and_type(self):
        """Process audio and transcribe"""
        if not self.audio_frames:
            print("No audio recorded")
            return
        
        original_duration = len(self.audio_frames) * self.chunk / self.sample_rate
        if original_duration < 0.5:
            print("Recording too short")
            return
        
        print(f"Processing {original_duration:.1f}s of audio...")
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as original_tmp:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as processed_tmp:
                try:
                    # Save original recording
                    wf = wave.open(original_tmp.name, 'wb')
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.audio_frames))
                    wf.close()
                    
                    # Process with FFmpeg
                    print("Removing silence, normalizing, and optimizing...")
                    if self.process_audio_with_ffmpeg(original_tmp.name, processed_tmp.name):
                        # Check processed duration
                        processed_duration = self.get_audio_duration(processed_tmp.name)
                        
                        if processed_duration > 0:
                            original_cost = original_duration * 0.006 / 60
                            processed_cost = processed_duration * 0.006 / 60
                            savings = ((original_cost - processed_cost) / original_cost) * 100 if original_cost > 0 else 0
                            
                            print(f"Original: {original_duration:.1f}s (${original_cost:.4f})")
                            print(f"Processed: {processed_duration:.1f}s (${processed_cost:.4f})")
                            print(f"Savings: {savings:.1f}%")
                            
                            # Transcribe processed audio
                            with open(processed_tmp.name, "rb") as audio_file:
                                transcript = self.client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    response_format="text"
                                )
                        else:
                            print("Processed audio is empty, using original")
                            with open(original_tmp.name, "rb") as audio_file:
                                transcript = self.client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    response_format="text"
                                )
                    else:
                        print("Processing failed, using original audio")
                        with open(original_tmp.name, "rb") as audio_file:
                            transcript = self.client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text"
                            )
                    
                    text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
                    
                    if text:
                        print(f"Transcribed: {text}")
                        time.sleep(0.1)
                        self.keyboard.type(text)
                    else:
                        print("No speech detected")
                        
                except Exception as e:
                    print(f"Transcription error: {e}")
                finally:
                    # Clean up temp files
                    for tmp_file in [original_tmp.name, processed_tmp.name]:
                        if os.path.exists(tmp_file):
                            os.unlink(tmp_file)

    def on_key_press(self, key):
        """Handle key press events"""
        try:
            if key == keyboard.Key.f1 and not self.is_recording:
                self.is_recording = True
                threading.Thread(target=self.record_audio, daemon=True).start()
        except AttributeError:
            pass

    def on_key_release(self, key):
        """Handle key release events"""
        try:
            if key == keyboard.Key.f1 and self.is_recording:
                self.is_recording = False
                print("Processing with silence removal...")
                threading.Thread(target=self.transcribe_and_type, daemon=True).start()
            elif key == keyboard.Key.esc:
                print("Goodbye!")
                os._exit(0)
        except AttributeError:
            pass

    def run(self):
        """Start the speech-to-text service"""
        with keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        ) as listener:
            listener.join()

def main():
    try:
        # Check dependencies
        for cmd in ['ffmpeg', 'ffprobe']:
            result = subprocess.run([cmd, '-version'], capture_output=True)
            if result.returncode != 0:
                print(f"{cmd} not found. Install with: sudo pacman -S ffmpeg")
                return
                
        stt = SilenceOptimizedSpeechToText()
        stt.run()
    except ValueError as e:
        print(f"Error: {e}")
        print("Set API key: export OPENAI_API_KEY='your-key-here'")
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
