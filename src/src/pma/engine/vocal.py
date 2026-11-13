"""Mastering ścieżek wokalu (styl BandLab): EQ, de-esser, kompresja, nasycenie, blask
+ efekty (pogłos / echo) renderowane OSOBNO jako ścieżka „wet”, żeby suwak efektu
i suwak głośności działały na żywo, a scalenie dawało identyczny wynik."""
import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field

import numpy as np
import soundfile as sf
from scipy import signal

from . import dsp
from .. import log as L
from ..i18n import count

WORK_LUFS = -22.0      # poziom roboczy przed kompresją
DRY_LUFS = -20.0       # poziom każdej przetworzonej ścieżki (suwak 0 dB = ten poziom)
CEILING_DBTP = -1.0
CACHE = os.path.join(os.path.expanduser("~/.cache"), "linux-project-mastering-audio", "vocal")


@dataclass
class VocalPreset:
    key: str
    hp: float
    eq: list
    deess: float              # próg de-essera (dB nad średnią pasma) – mniejszy = mocniej
    comp_thr: float
    comp_ratio: float
    attack_ms: float
    release_ms: float
    saturation: float
    reverb: dict = field(default_factory=dict)   # size_s, predelay_ms, damp_hz, mix
    delay: dict = field(default_factory=dict)    # time_ms, feedback, pingpong, mix
    fx_default: int = 20      # domyślna pozycja suwaka pogłosu/echa (0–100)


PRESETS = {
    "studio": VocalPreset(
        "studio", hp=90, eq=[("peak", 300, -2.0, 1.2), ("peak", 3500, 2.0, 1.0), ("high", 12000, 2.5, 0.7)],
        deess=6.0, comp_thr=-24, comp_ratio=3.0, attack_ms=8, release_ms=120, saturation=0.1,
        reverb=dict(size_s=1.3, predelay_ms=25, damp_hz=7000, mix=1.0), delay={}, fx_default=15),
    "radio": VocalPreset(
        "radio", hp=100, eq=[("peak", 350, -2.5, 1.2), ("peak", 2500, 3.0, 0.9), ("high", 11000, 4.0, 0.7)],
        deess=4.5, comp_thr=-26, comp_ratio=4.0, attack_ms=4, release_ms=90, saturation=0.2,
        reverb=dict(size_s=0.9, predelay_ms=15, damp_hz=8000, mix=0.6),
        delay=dict(time_ms=110, feedback=0.0, pingpong=False, mix=0.5), fx_default=20),
    "warm": VocalPreset(
        "warm", hp=70, eq=[("peak", 180, 1.5, 0.9), ("peak", 450, -1.5, 1.2), ("peak", 3000, 1.0, 1.0),
                           ("high", 9000, -1.0, 0.7)],
        deess=6.0, comp_thr=-24, comp_ratio=2.5, attack_ms=15, release_ms=180, saturation=0.35,
        reverb=dict(size_s=2.2, predelay_ms=35, damp_hz=5500, mix=1.0), delay={}, fx_default=28),
    "space": VocalPreset(
        "space", hp=110, eq=[("peak", 300, -2.0, 1.2), ("peak", 4000, 1.5, 1.0), ("high", 11000, 3.0, 0.7)],
        deess=5.0, comp_thr=-25, comp_ratio=3.0, attack_ms=8, release_ms=140, saturation=0.1,
        reverb=dict(size_s=3.2, predelay_ms=45, damp_hz=6500, mix=0.8),
        delay=dict(time_ms=375, feedback=0.38, pingpong=True, mix=0.55), fx_default=40),
    "rap": VocalPreset(
        "rap", hp=110, eq=[("peak", 400, -3.0, 1.2), ("peak", 4000, 3.5, 0.9), ("high", 10000, 2.0, 0.7)],
        deess=4.0, comp_thr=-27, comp_ratio=5.0, attack_ms=3, release_ms=70, saturation=0.3,
        reverb=dict(size_s=0.6, predelay_ms=10, damp_hz=8000, mix=0.6),
        delay=dict(time_ms=90, feedback=0.0, pingpong=False, mix=0.45), fx_default=12),
    "pop": VocalPreset(
        "pop", hp=100, eq=[("peak", 250, -2.0, 1.1), ("peak", 3000, 2.5, 1.0), ("high", 12000, 3.5, 0.7)],
        deess=4.5, comp_thr=-26, comp_ratio=4.0, attack_ms=5, release_ms=100, saturation=0.15,
        reverb=dict(size_s=1.4, predelay_ms=20, damp_hz=8000, mix=0.8),
        delay=dict(time_ms=180, feedback=0.15, pingpong=False, mix=0.35), fx_default=22),
    "acoustic": VocalPreset(
        "acoustic", hp=80, eq=[("peak", 250, -1.0, 1.0), ("peak", 3500, 1.0, 1.0), ("high", 12000, 1.5, 0.7)],
        deess=6.5, comp_thr=-22, comp_ratio=2.0, attack_ms=15, release_ms=160, saturation=0.05,
        reverb=dict(size_s=1.6, predelay_ms=20, damp_hz=7000, mix=1.0), delay={}, fx_default=18),
    "rnb": VocalPreset(
        "rnb", hp=85, eq=[("peak", 200, 1.0, 0.9), ("peak", 500, -1.5, 1.2), ("peak", 3500, 1.5, 1.0),
                          ("high", 11000, 2.0, 0.7)],
        deess=5.0, comp_thr=-25, comp_ratio=3.5, attack_ms=10, release_ms=150, saturation=0.25,
        reverb=dict(size_s=2.6, predelay_ms=40, damp_hz=6000, mix=1.0),
        delay=dict(time_ms=330, feedback=0.3, pingpong=True, mix=0.4), fx_default=30),
    "podcast": VocalPreset(
        "podcast", hp=90, eq=[("peak", 300, -2.5, 1.2), ("peak", 3000, 2.0, 1.0), ("high", 10000, 1.0, 0.7)],
        deess=4.0, comp_thr=-28, comp_ratio=4.0, attack_ms=5, release_ms=80, saturation=0.1,
        reverb={}, delay={}, fx_default=0),
    "lofi": VocalPreset(
        "lofi", hp=200, eq=[("peak", 1000, 2.0, 0.8), ("high", 7000, -6.0, 0.7)],
        deess=6.0, comp_thr=-26, comp_ratio=4.0, attack_ms=10, release_ms=120, saturation=0.5,
        reverb=dict(size_s=0.8, predelay_ms=10, damp_hz=4000, mix=0.7),
        delay=dict(time_ms=250, feedback=0.25, pingpong=False, mix=0.4), fx_default=25),
}
PRESET_ORDER = ["studio", "radio", "warm", "space", "rap", "pop", "acoustic", "rnb", "podcast", "lofi", "manual"]

# MANUAL: suwaki w kaflach (zakładka Wokal). Wartości startowe = „Studio”.
MANUAL_DEFAULT = dict(lowcut=90.0, body=0.0, mud=-2.0, presence=2.0, air=2.5,
                      deess=50.0, comp_thr=-24.0, comp_ratio=3.0, attack=8.0, release=120.0, saturation=10.0,
                      reverb_size=1.3, predelay=25.0, echo_ms=0.0, echo_fb=0.0)
# (klucz, min, max, krok) – zakresy suwaków
MANUAL_RANGES = {
    "lowcut": (40, 250, 5), "body": (-6, 6, 0.5), "mud": (-8, 4, 0.5), "presence": (-6, 8, 0.5), "air": (-6, 8, 0.5),
    "deess": (0, 100, 5), "comp_thr": (-40, -10, 1), "comp_ratio": (1, 8, 0.5), "attack": (1, 50, 1),
    "release": (40, 400, 10), "saturation": (0, 60, 1),
    "reverb_size": (0, 4, 0.1), "predelay": (0, 100, 5), "echo_ms": (0, 600, 10), "echo_fb": (0, 0.7, 0.05),
}


def manual_preset(m):
    """Słownik z suwaków -> VocalPreset. Pogłos 0 s i echo 0 ms = wyłączone."""
    m = {**MANUAL_DEFAULT, **(m or {})}
    reverb = dict(size_s=m["reverb_size"], predelay_ms=m["predelay"], damp_hz=7000, mix=1.0) \
        if m["reverb_size"] >= 0.2 else {}
    delay = dict(time_ms=m["echo_ms"], feedback=m["echo_fb"], pingpong=m["echo_fb"] > 0.2, mix=0.5) \
        if m["echo_ms"] >= 20 else {}
    return VocalPreset(
        "manual", hp=m["lowcut"],
        eq=[("peak", 200, m["body"], 0.9), ("peak", 350, m["mud"], 1.2), ("peak", 3500, m["presence"], 1.0),
            ("high", 12000, m["air"], 0.7)],
        deess=9.0 - 0.07 * m["deess"] if m["deess"] > 0 else 60.0,     # 100% -> próg 2 dB, 0% -> praktycznie wyłączony
        comp_thr=m["comp_thr"], comp_ratio=m["comp_ratio"], attack_ms=m["attack"], release_ms=m["release"],
        saturation=m["saturation"] / 100.0, reverb=reverb, delay=delay, fx_default=20)


def get_preset(key, manual=None):
    return manual_preset(manual) if key == "manual" else PRESETS[key]


def fx_gain(fx):
    """Pozycja suwaka 0–100 -> wzmocnienie ścieżki wet (krzywa „na ucho”)."""
    fx = max(0.0, min(100.0, float(fx))) / 100.0
    return fx ** 1.6


# ----------------------------------------------------------------- przetwarzanie
def deesser(x, fs, thr_db, ratio=4.0, f0=5500):
    """Dynamiczne przyciszanie syczących głosek (s, sz, cz) w paśmie > f0."""
    sos = signal.butter(2, f0, "highpass", fs=fs, output="sos")
    hb = signal.sosfilt(sos, x, axis=0)
    blk = max(16, int(fs * 0.003))
    n = len(x)
    nb = (n + blk - 1) // blk
    pad = lambda a: np.concatenate([a, np.zeros((nb * blk - n, a.shape[1]))])  # noqa: E731
    e_hb = 10 * np.log10((pad(hb) ** 2).reshape(nb, blk, -1).mean(axis=(1, 2)) + 1e-12)
    e_all = 10 * np.log10((pad(x) ** 2).reshape(nb, blk, -1).mean(axis=(1, 2)) + 1e-12)
    rel = e_hb - e_all
    base = np.median(rel[e_all > e_all.max() - 40]) if np.any(e_all > e_all.max() - 40) else 0.0
    over = rel - (base + thr_db)
    gr = np.where(over > 0, -over * (1 - 1 / ratio), 0.0)
    gr = np.maximum(gr, -10.0)
    sm = np.empty_like(gr)
    g = 0.0
    aa, ar = math.exp(-blk / fs / 0.001), math.exp(-blk / fs / 0.06)
    for i, v in enumerate(gr.tolist()):
        g = aa * g + (1 - aa) * v if v < g else ar * g + (1 - ar) * v
        sm[i] = g
    gs = 10 ** (np.interp(np.arange(n), np.arange(nb) * blk + blk / 2, sm) / 20)
    return (x - hb + hb * gs[:, None]).astype(np.float32)


def _reverb_ir(fs, size_s, predelay_ms, damp_hz, seed=11):
    rng = np.random.default_rng(seed)
    n = int(fs * size_s)
    t = np.arange(n) / fs
    env = np.exp(-6.91 * t / size_s)                      # -60 dB po size_s
    ir = rng.standard_normal((n, 2)) * env[:, None]
    # tłumienie wysokich: im później, tym ciemniej (dwa pasma)
    lo = signal.sosfilt(signal.butter(2, damp_hz, "lowpass", fs=fs, output="sos"), ir, axis=0)
    hi = ir - lo
    hi *= np.exp(-6.91 * t / (size_s * 0.35))[:, None]
    ir = lo + hi
    # wczesne odbicia
    for k, (ms, g) in enumerate([(7, 0.5), (13, 0.4), (19, 0.33), (29, 0.25), (37, 0.2)]):
        i = int(fs * ms / 1000)
        ir[i, k % 2] += g * 3
    pre = np.zeros((int(fs * predelay_ms / 1000), 2))
    ir = np.vstack([pre, ir])
    return ir / np.sqrt((ir ** 2).sum() / 2)


def _delay(x, fs, time_ms, feedback, pingpong, repeats=6):
    d = int(fs * time_ms / 1000)
    src = signal.sosfilt(signal.butter(2, [250, 6000], "bandpass", fs=fs, output="sos"), x.mean(axis=1))
    out = np.zeros((len(x) + d * (repeats + 1), 2))
    g = 1.0
    reps = 1 if feedback <= 0 else repeats
    lp = signal.butter(1, 4500, "lowpass", fs=fs, output="sos")
    s = src
    for k in range(1, reps + 1):
        ch = (k % 2) if pingpong else None
        a = k * d
        if ch is None:
            out[a:a + len(s)] += (g * s)[:, None] * 0.7071
        else:
            out[a:a + len(s), ch] += g * s
        g *= feedback if feedback > 0 else 0
        s = signal.sosfilt(lp, s)
        if g < 0.02:
            break
    return out[:len(x)]


def render_wet(dry, fs, p, name=""):
    """Ścieżka efektu (pogłos + echo), znormalizowana do głośności suchej ścieżki."""
    if not p.reverb and not p.delay:
        return np.zeros_like(dry)
    send = signal.sosfilt(signal.butter(2, [180, 9000], "bandpass", fs=fs, output="sos"), dry, axis=0)
    wet = np.zeros((len(dry), 2))
    if p.reverb:
        L.log(f"{name}: pogłos {p.reverb['size_s']:g} s, predelay {p.reverb['predelay_ms']:g} ms", tag="fx")
        ir = _reverb_ir(fs, p.reverb["size_s"], p.reverb["predelay_ms"], p.reverb["damp_hz"])
        m = send.mean(axis=1)
        for c in range(2):
            wet[:, c] += p.reverb["mix"] * signal.oaconvolve(m, ir[:, c])[:len(dry)]
    if p.delay:
        L.log(f"{name}: echo {p.delay['time_ms']:g} ms, feedback {p.delay['feedback']:.2f}"
              f"{', ping-pong' if p.delay['pingpong'] else ''}", tag="fx")
        wet += p.delay["mix"] * _delay(send, fs, p.delay["time_ms"], p.delay["feedback"], p.delay["pingpong"])
    l_wet = dsp.integrated_lufs(wet, fs)
    if l_wet > -69:
        wet *= dsp.undb(DRY_LUFS - 6.0 - l_wet)   # 100% efektu = 6 dB ciszej niż wokal
    return wet.astype(np.float32)


def process_dry(x, fs, p, name=""):
    x = dsp.apply_sos(x.astype(np.float32), [dsp.highpass(fs, p.hp, 2)])
    x = dsp.apply_sos(x, dsp.eq_chain(fs, p.eq))
    eq = ", ".join(f"{f:g} Hz {g:+.1f}" for _k, f, g, _q in p.eq)
    L.log(f"{name}: filtr {p.hp:g} Hz, EQ [{eq}]", tag="vocal")
    l0 = dsp.integrated_lufs(x, fs)
    if l0 > -69:
        x = (x * dsp.undb(WORK_LUFS - l0)).astype(np.float32)
    x = deesser(x, fs, p.deess)
    x, gr = dsp.compressor(x, fs, p.comp_thr, p.comp_ratio, p.attack_ms, p.release_ms, knee_db=6.0)
    L.log(f"{name}: de-esser, kompresja {p.comp_ratio:g}:1 (redukcja do {gr:.1f} dB)", tag="vocal")
    x = deesser(x, fs, p.deess + 2.0)        # drugi, lżejszy przebieg po kompresji
    x = dsp.saturate(x, p.saturation)
    l1 = dsp.integrated_lufs(x, fs)
    if l1 > -69:
        x = (x * dsp.undb(DRY_LUFS - l1)).astype(np.float32)
    return x


def load_vocal(path, fs_target=None):
    x, fs = sf.read(path, dtype="float32", always_2d=True)
    x = x[:, :2]
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)            # mono -> środek panoramy
    if fs_target and fs != fs_target:
        g = math.gcd(fs, fs_target)
        x = signal.resample_poly(x, fs_target // g, fs // g, axis=0).astype(np.float32)
        fs = fs_target
    return x, fs


def render_track(path, preset_key, fs_target, manual=None):
    """Renderuje (z cache) suchą i mokrą wersję ścieżki. Zwraca (dry.wav, wet.wav, sekundy).
    preset_key == 'manual' -> ustawienia z suwaków (słownik `manual`, wchodzi do klucza cache)."""
    extra = json.dumps({**MANUAL_DEFAULT, **(manual or {})}, sort_keys=True) if preset_key == "manual" else ""
    key = hashlib.sha1(f"{path}|{os.path.getmtime(path)}|{preset_key}|{fs_target}|{extra}|v1".encode()).hexdigest()[:16]
    d = os.path.join(CACHE, key)
    dry_p, wet_p = os.path.join(d, "dry.wav"), os.path.join(d, "wet.wav")
    name = os.path.basename(path)
    if os.path.exists(dry_p) and os.path.exists(wet_p):
        L.log(f"{name}: {preset_key} z cache ({key})", tag="vocal")
        return dry_p, wet_p, sf.info(dry_p).duration
    t0 = time.time()
    L.log(f"{name}: start, opcja '{preset_key}', {fs_target} Hz", tag="vocal")
    os.makedirs(d, exist_ok=True)
    x, fs = load_vocal(path, fs_target)
    L.log(f"{name}: wczytano {len(x) / fs:.1f} s, {dsp.integrated_lufs(x, fs):.1f} LUFS, "
          f"szczyt {dsp.true_peak_db(x):.1f} dBTP", tag="vocal")
    p = get_preset(preset_key, manual)
    dry = process_dry(x, fs, p, name)
    wet = render_wet(dry, fs, p, name)
    sf.write(dry_p + ".tmp.wav", dry, fs, subtype="FLOAT")
    sf.write(wet_p + ".tmp.wav", wet, fs, subtype="FLOAT")
    os.replace(dry_p + ".tmp.wav", dry_p)
    os.replace(wet_p + ".tmp.wav", wet_p)
    L.log(f"{name}: gotowe w {time.time() - t0:.1f} s", "ok", tag="vocal")
    return dry_p, wet_p, len(dry) / fs


def merge(tracks, out_path, fs):
    """tracks: lista dict(dry, wet, volume_db, fx). Sumuje dokładnie tak jak odsłuch na żywo,
    potem zabezpiecza szczyty (limiter true-peak -1 dBTP tylko gdy potrzeba). WAV 24 bit."""
    parts = []
    for t in tracks:
        dry, _ = sf.read(t["dry"], dtype="float32", always_2d=True)
        wet, _ = sf.read(t["wet"], dtype="float32", always_2d=True)
        v = dsp.undb(t["volume_db"])
        parts.append(dry * v + wet * (v * fx_gain(t["fx"])))
    n = max(len(p) for p in parts)
    mix = np.zeros((n, 2), dtype=np.float32)
    for p in parts:
        mix[:len(p)] += p
    tp_before = dsp.true_peak_db(mix)
    L.log(f"scalanie: {count(len(tracks), 'stem', 'pl')}, suma {n / fs:.1f} s, szczyt {tp_before:+.2f} dBTP", tag="merge")
    lim = 0.0
    if tp_before > CEILING_DBTP:
        mix, lim = dsp.limiter(mix, fs, CEILING_DBTP - 0.05, lookahead_ms=1.5, release_ms=60)
        L.log(f"limiter true-peak: redukcja {lim:.2f} dB -> {CEILING_DBTP} dBTP", "warn", tag="merge")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    sf.write(out_path, mix, fs, subtype="PCM_24")
    L.log(f"zapisano {os.path.basename(out_path)} (WAV 24 bit, {fs} Hz)", "ok", tag="merge")
    return dict(path=out_path, lufs=dsp.integrated_lufs(mix, fs), true_peak=dsp.true_peak_db(mix),
                limited_db=lim, peak_before=tp_before, seconds=n / fs)
