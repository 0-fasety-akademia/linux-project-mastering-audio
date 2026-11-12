"""Normalizacja głośności całego albumu (już zmiksowane / zmasterowane utwory).
Bez EQ i bez kompresji – tylko wzmocnienie do celu + limiter true-peak, gdy trzeba."""
import os
from dataclasses import dataclass

import numpy as np

from . import dsp
from .. import log as L
from .export import export_track
from .common import load, loud_level

CEILING_DBTP = -1.0

# docelowa głośność zintegrowana (LUFS)
TARGETS = {
    "streaming": -14.0,   # Spotify, YouTube, Tidal, Amazon
    "apple": -16.0,       # Apple Music / iTunes Sound Check
    "cd": -10.0,          # CD / pliki „jak ze sklepu”
    "loud": -8.0,         # bardzo głośno (klub, rap, EDM)
}
TARGET_ORDER = ["streaming", "apple", "cd", "loud"]
MODES = ["loud_parts", "integrated", "album_gain"]
# loud_parts  – refreny / głośne fragmenty wszystkich utworów na tym samym poziomie (zalecane)
# integrated  – identyczna średnia głośność (LUFS) każdego utworu
# album_gain  – jedno wspólne wzmocnienie dla całej płyty (zachowuje różnice z miksu)


@dataclass
class NormInfo:
    path: str
    fs: int = 0
    duration: float = 0.0
    lufs: float = -70.0
    loud: float = -70.0
    true_peak: float = -120.0
    error: str = ""


def analyze(path):
    i = NormInfo(path)
    try:
        x, fs = load(path)
        i.fs, i.duration = fs, len(x) / fs
        i.lufs = dsp.integrated_lufs(x, fs)
        i.loud = loud_level(x, fs)
        i.true_peak = dsp.true_peak_db(x)
        L.log(f"{os.path.basename(path)}: {i.lufs:.1f} LUFS, refren {i.loud:.1f}, szczyt {i.true_peak:+.2f} dBTP",
              "warn" if i.true_peak > 0 else "info", tag="analiza")
    except Exception as e:  # noqa: BLE001
        i.error = str(e)
        L.log(f"{os.path.basename(path)}: błąd {e}", "error", tag="analiza")
    return i


def plan(infos, target_key, mode):
    """Zwraca {ścieżka: (rodzaj_pomiaru, wartość_docelowa)}."""
    t = TARGETS[target_key]
    ok = [i for i in infos if not i.error]
    out = {}
    if mode == "album_gain" and ok:
        # najgłośniejszy utwór trafia w cel, reszta dostaje to samo wzmocnienie
        g = t - max(i.lufs for i in ok)
        for i in ok:
            out[i.path] = ("gain", g)
    elif mode == "integrated":
        for i in ok:
            out[i.path] = ("lufs", t)
    else:
        for i in ok:
            out[i.path] = ("loud", t + 1.0)     # refren ≈ 1 LU głośniej niż średnia
    return out


def _protect(y, fs):
    """Miękki clipper (ścina tylko pojedyncze transjenty) + limiter true-peak."""
    y = dsp.soft_clip(y, -0.3, 0.8)
    return dsp.limiter(y, fs, CEILING_DBTP - 0.05)


def _measure(kind, y, fs):
    return loud_level(y, fs) if kind == "loud" else dsp.integrated_lufs(y, fs)


def normalize(x, fs, kind, value, name=""):
    """Wzmocnienie (iteracyjnie, bo limiter zjada część) + limiter -1 dBTP."""
    if kind == "gain":
        y = (x * dsp.undb(value)).astype(np.float32)
        lim = 0.0
        if dsp.true_peak_db(y) > CEILING_DBTP:
            y, lim = _protect(y, fs)
        return y, lim
    cur = _measure(kind, x, fs)
    gain = value - cur
    y, lim = x, 0.0
    hist = []
    for _ in range(8):
        y = (x * dsp.undb(gain)).astype(np.float32)
        lim = 0.0
        if dsp.true_peak_db(y) > CEILING_DBTP:
            y, lim = _protect(y, fs)
        got = _measure(kind, y, fs)
        err = value - got
        L.log(f"{name}: wzmocnienie {gain:+.2f} dB -> {got:.2f} (limiter {lim:.1f} dB)", tag="album")
        if abs(err) < 0.1:
            break
        hist.append((gain, got))
        if len(hist) >= 2 and abs(hist[-1][1] - hist[-2][1]) > 1e-3 and hist[-1][0] != hist[-2][0]:
            (g1, l1), (g2, l2) = hist[-2], hist[-1]
            gain = g2 + err / max((l2 - l1) / (g2 - g1), 0.15)
        else:
            gain += err * 1.3
        gain = min(gain, value - cur + 18)      # bez absurdalnego dociskania
    return y, lim


def _job(idx, info_path, kind, value, out_dir, formats, wav_quality, cover, meta, total, title):
    name = os.path.basename(info_path)
    L.log(f"{name}: start ({kind} -> {value:+.1f})", tag="album")
    x, fs = load(info_path)
    y, lim = normalize(x, fs, kind, value, name)
    stem = os.path.splitext(os.path.basename(info_path))[0]
    tags = dict(title=title, artist=meta.get("artist", ""), album=meta.get("album", ""),
                tracknumber=f"{idx + 1}/{total}")
    files = export_track(y, fs, out_dir, stem, formats, wav_quality, cover, tags)
    for fmt, f in files.items():
        L.log(f"{name}: {fmt.upper()} zapisany, true peak {f['true_peak']:.2f} dBTP", "ok", tag="export")
    st = dict(lufs=dsp.integrated_lufs(y, fs), loud=loud_level(y, fs), true_peak=dsp.true_peak_db(y), limited=lim)
    return idx, st, files
