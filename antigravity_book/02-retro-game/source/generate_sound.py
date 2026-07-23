import wave
import math
import struct
import os

def generate_beep(filename, duration=0.1, frequency=880, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            # Sine wave
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
            
    print(f"Generated {filename}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sound_dir = os.path.join(base_dir, "assets", "sounds")
    generate_beep(os.path.join(sound_dir, "shoot.wav"), duration=0.1, frequency=1200)
    generate_beep(os.path.join(sound_dir, "explosion.wav"), duration=0.3, frequency=200) # Optional low freq for explosion
