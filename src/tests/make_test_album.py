"""Generuje syntetyczny „album studyjny” do testów (różne poziomy i barwy)."""
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal


def song(seconds, fs, bpm, level_db, tilt, seed, ballad=False):
    rng = np.random.default_rng(seed)
    n = int(seconds * fs)
    t = np.arange(n) / fs
    beat = 60 / bpm
    out = np.zeros((n, 2))
    # akordy (pad)
    roots = [110, 87.3, 130.8, 98]
    for i, r in enumerate(roots * int(seconds / (4 * beat * 4) + 1)):
        s, e = int(i * 4 * beat * 4 * fs / 4), int((i + 1) * 4 * beat * 4 * fs / 4)
        if s >= n:
            break
        e = min(e, n)
        tt = t[s:e]
        for k, m in enumerate([1, 1.25, 1.5, 2, 3]):
            ph = rng.random() * 6
            out[s:e, 0] += 0.06 * np.sin(2 * np.pi * r * 2 * m * tt + ph) / (k + 1) ** 0.5
            out[s:e, 1] += 0.06 * np.sin(2 * np.pi * r * 2 * m * 1.002 * tt + ph) / (k + 1) ** 0.5
        bass = signal.sawtooth(2 * np.pi * r / 2 * tt) * 0.18
        out[s:e] += bass[:, None]
    if not ballad:
        for b in np.arange(0, seconds, beat):
            i = int(b * fs)
            L = min(int(0.25 * fs), n - i)
            tt = np.arange(L) / fs
            kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) * 0.9
            out[i:i + L] += kick[:, None]
            if int(round(b / beat)) % 2 == 1:
                sn = rng.standard_normal(L) * np.exp(-tt * 18) * 0.45
                out[i:i + L] += sn[:, None]
            h = int((b + beat / 2) * fs)
            if h < n:
                Lh = min(int(0.05 * fs), n - h)
                hat = rng.standard_normal(Lh) * np.exp(-np.arange(Lh) / fs * 80) * 0.15
                out[h:h + Lh, 0] += hat
                out[h:h + Lh, 1] += hat * 0.7
    # „wokal” – modulowany ton
    vib = np.sin(2 * np.pi * 5 * t) * 4
    mel = 330 + 60 * np.sign(np.sin(2 * np.pi * t / (beat * 8)))
    voc = np.sin(2 * np.pi * np.cumsum(mel + vib) / fs) * 0.12 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 7) ** 2)
    out += voc[:, None]
    # barwa miksu (tilt) – różne realizacje
    if tilt:
        sos = signal.butter(1, 1500, "highpass" if tilt > 0 else "lowpass", fs=fs, output="sos")
        out = out + abs(tilt) * signal.sosfilt(sos, out, axis=0)
    out *= 10 ** (level_db / 20) / np.max(np.abs(out))
    return out.astype(np.float32)


if __name__ == "__main__":
    d = sys.argv[1]
    os.makedirs(d, exist_ok=True)
    fs = 48000
    sf.write(f"{d}/01 Otwarcie.wav", song(70, fs, 120, -3, 0.0, 1), fs, subtype="PCM_24")
    sf.write(f"{d}/02 Ciemny numer.wav", song(60, fs, 100, -6, -1.5, 2), fs, subtype="PCM_24")
    sf.write(f"{d}/03 Jasny numer.wav", song(60, fs, 128, -1, 1.5, 3), fs, subtype="PCM_24")
    sf.write(f"{d}/04 Ballada.wav", song(60, fs, 70, -9, 0.0, 4, ballad=True), fs, subtype="PCM_24")
    print("ok")
