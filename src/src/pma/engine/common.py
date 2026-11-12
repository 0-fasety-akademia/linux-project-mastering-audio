"""Wspólne narzędzia: wczytywanie, głośność głośnych fragmentów, zabezpieczenie szczytów, resampling."""
import math

import numpy as np
import soundfile as sf
from scipy import signal

from . import dsp

CEILING_DBTP = -1.0


def load(path):
    x, fs = sf.read(path, dtype="float32", always_2d=True)
    if x.shape[1] > 2:
        x = x[:, :2]
    return x, fs


def loud_level(x, fs):
    """Głośność głośnych fragmentów: 95. percentyl short-term (3 s) LUFS."""
    st = dsp.short_term(x, fs, 0.5)
    st = st[st > -70]
    if st.size == 0:
        return -70.0
    return float(np.percentile(st, 95))


def safety_limit(x, fs):
    """Ostateczne zabezpieczenie po zmianie częstotliwości (zwykle nic nie robi)."""
    if dsp.true_peak_db(x) <= CEILING_DBTP:
        return x
    y, _ = dsp.limiter(x, fs, CEILING_DBTP - 0.05)
    return y


def to_rate(x, fs, new_fs):
    if fs == new_fs:
        return x
    g = math.gcd(int(fs), int(new_fs))
    return signal.resample_poly(x.astype(np.float64), new_fs // g, fs // g, axis=0).astype(np.float32)
