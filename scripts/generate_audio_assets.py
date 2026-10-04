import numpy as np
import scipy.io.wavfile as wavfile
import os

os.makedirs("videos/continuum_showcase/assets", exist_ok=True)
sr = 48000

# 1. Subtle UI Whoosh (0.35s)
def create_whoosh(duration=0.35):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Pink noise approximation with smooth resonant sweep
    noise = np.random.normal(0, 1, len(t))
    sweep = 200 + 800 * (1 / (1 + np.exp(-15 * (t - duration/2))))
    # Envelope
    env = np.sin(np.pi * (t / duration)) ** 2
    # Simple lowpass filter effect
    sig = noise * np.sin(2 * np.pi * sweep * t) * env
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.4
    return (sig * 32767).astype(np.int16)

# 2. Digital Telemetry Blip (0.06s)
def create_blip(duration=0.06):
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = 1400 - 800 * (t / duration)
    sig = np.sin(2 * np.pi * freq * t) * np.exp(-t * 50)
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.35
    return (sig * 32767).astype(np.int16)

# 3. High-Tech Confirmation Chime (0.6s)
def create_chime(duration=0.6):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Harmonics: 587 Hz (D5) + 880 Hz (A5) + 1175 Hz (D6)
    sig = (
        0.5 * np.sin(2 * np.pi * 587.33 * t) * np.exp(-t * 6) +
        0.35 * np.sin(2 * np.pi * 880.00 * t) * np.exp(-t * 8) +
        0.2 * np.sin(2 * np.pi * 1174.66 * t) * np.exp(-t * 12)
    )
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.45
    return (sig * 32767).astype(np.int16)

# 4. Cinematic Minimal Tech Ambient Music Bed (135.0s)
def create_bgm(duration=135.0):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Warm sub-bass drone (55 Hz A1 + 110 Hz A2)
    drone1 = np.sin(2 * np.pi * 55.0 * t) * 0.35
    drone2 = np.sin(2 * np.pi * 110.0 * t + 0.5) * 0.15
    # Gentle subtle lfo swell
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.08 * t)
    drone = (drone1 + drone2) * lfo

    # High ethereal shimmer chords (harmonic bed)
    shimmer = (
        0.08 * np.sin(2 * np.pi * 440.0 * t) +
        0.06 * np.sin(2 * np.pi * 659.25 * t) +
        0.05 * np.sin(2 * np.pi * 880.0 * t)
    ) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t + 1.0))

    # Minimal rhythmic tech pulse at 110 BPM (approx 1.833 Hz pulse)
    bpm = 110
    beat_interval = 60.0 / bpm
    pulse_indices = np.arange(0, duration, beat_interval)
    pulse = np.zeros_like(t)
    for p in pulse_indices:
        idx = int(p * sr)
        p_len = int(0.04 * sr)
        if idx + p_len < len(pulse):
            pt = np.linspace(0, 0.04, p_len, False)
            pulse[idx:idx+p_len] += np.sin(2 * np.pi * 800 * pt) * np.exp(-pt * 90) * 0.08

    # Combine into pristine stereo bed
    left = (drone + shimmer + pulse) * 0.4
    right = (drone + shimmer * 0.9 + pulse) * 0.4

    # Smooth 2s fade-in and 3s fade-out
    fade_in = np.clip(t / 2.0, 0, 1)
    fade_out = np.clip((duration - t) / 3.0, 0, 1)
    env = fade_in * fade_out

    left = left * env
    right = right * env

    stereo = np.column_stack([left, right])
    stereo = stereo / (np.max(np.abs(stereo)) + 1e-6) * 0.5
    return (stereo * 32767).astype(np.int16)

wavfile.write("videos/continuum_showcase/assets/whoosh.wav", sr, create_whoosh())
wavfile.write("videos/continuum_showcase/assets/blip.wav", sr, create_blip())
wavfile.write("videos/continuum_showcase/assets/chime.wav", sr, create_chime())
wavfile.write("videos/continuum_showcase/assets/bgm.wav", sr, create_bgm())

print("Generated audio assets in videos/continuum_showcase/assets/")
