"""Syntetyczne ścieżki wokalu (mono, z głoskami „s”) do testów."""
import sys
import numpy as np
import soundfile as sf
from scipy import signal


def vocal(seconds, fs, f0, seed, sparse=False, level=-6):
    rng = np.random.default_rng(seed)
    n = int(seconds * fs); t = np.arange(n) / fs
    pitch = f0 * (1 + 0.25 * np.sign(np.sin(2 * np.pi * t / 1.7))) * (1 + 0.01 * np.sin(2 * np.pi * 5.5 * t))
    src = signal.sawtooth(2 * np.pi * np.cumsum(pitch) / fs)
    out = np.zeros(n)
    for fc, bw, g in ((700, 130, 1.0), (1200, 150, 0.6), (2600, 250, 0.35)):
        out += g * signal.sosfilt(signal.butter(2, [fc - bw, fc + bw], "bandpass", fs=fs, output="sos"), src)
    syl = (np.sin(2 * np.pi * t * 2.2) > -0.3).astype(float)
    syl = signal.sosfilt(signal.butter(1, 30, fs=fs, output="sos"), syl)
    if sparse:
        syl *= (np.sin(2 * np.pi * t / 6) > 0.6)
    out *= syl
    for s0 in np.arange(0.8, seconds, 1.9):
        i = int(s0 * fs); L = int(0.12 * fs)
        if i + L < n and (not sparse or syl[i] > 0.1):
            ss = signal.sosfilt(signal.butter(4, 5000, "highpass", fs=fs, output="sos"), rng.standard_normal(L))
            out[i:i + L] += ss * np.hanning(L) * 1.2
    out *= 10 ** (level / 20) / np.abs(out).max()
    return out.astype(np.float32)


d = sys.argv[1]; fs = 48000
sf.write(f"{d}/A wokal glowny.wav", vocal(60, fs, 180, 1), fs, subtype="PCM_24")
sf.write(f"{d}/B dopowiedzi.wav", vocal(60, fs, 230, 2, sparse=True, level=-9), fs, subtype="PCM_24")
sf.write(f"{d}/C chorki.wav", vocal(60, fs, 270, 3, level=-12), fs, subtype="PCM_24")
print("ok")
