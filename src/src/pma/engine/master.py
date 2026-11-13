"""Lekki mastering całego miksu (przed normalizacją): filtr subsoniczny, korekcja barwy,
kompresja „sklejająca” i delikatne nasycenie. Głośność zintegrowana wyniku = głośność wejścia,
więc wyrównanie płyty i przewidywane zmiany w trybie normalizacji nadal się zgadzają."""
from dataclasses import dataclass

import numpy as np

from . import dsp
from .. import log as L

WORK_LUFS = -18.0          # poziom roboczy przed kompresją (progi presetów są do niego dobrane)


@dataclass
class MasterPreset:
    key: str
    eq: list                # (typ, f0, gain_db, q) – typ: 'peak' | 'low' | 'high'
    comp_thr: float
    comp_ratio: float
    attack_ms: float
    release_ms: float
    saturation: float
    hp: float = 25.0        # filtr subsoniczny (dudnienie, DC)


PRESETS = {
    "gentle": MasterPreset(
        "gentle", eq=[("low", 90, 0.5, 0.7), ("peak", 300, -0.5, 1.0), ("high", 12000, 1.0, 0.7)],
        comp_thr=-13.0, comp_ratio=1.5, attack_ms=30, release_ms=250, saturation=0.05),
    "warm": MasterPreset(
        "warm", eq=[("low", 110, 1.5, 0.7), ("peak", 350, -1.0, 1.0), ("high", 9000, -0.8, 0.7)],
        comp_thr=-14.0, comp_ratio=2.0, attack_ms=25, release_ms=200, saturation=0.25),
    "modern": MasterPreset(
        "modern", eq=[("low", 60, 0.8, 0.7), ("peak", 280, -1.5, 1.0), ("peak", 3200, 1.0, 1.0),
                      ("high", 11000, 2.0, 0.7)],
        comp_thr=-13.0, comp_ratio=2.0, attack_ms=15, release_ms=150, saturation=0.12),
    "punch": MasterPreset(
        "punch", eq=[("low", 75, 1.5, 0.7), ("peak", 400, -1.5, 1.0), ("peak", 2500, 1.0, 1.0),
                     ("high", 10000, 1.0, 0.7)],
        comp_thr=-14.0, comp_ratio=2.5, attack_ms=10, release_ms=120, saturation=0.3),
}
ORDER = ["off", "gentle", "warm", "modern", "punch"]


def process(x, fs, key, name=""):
    """Zwraca (sygnał, redukcja kompresora w dB). key == 'off' -> bez zmian."""
    p = PRESETS.get(key)
    if p is None:
        return x, 0.0
    l_in = dsp.integrated_lufs(x, fs)
    if l_in <= -69:
        return x, 0.0
    y = dsp.apply_sos(x.astype(np.float32), [dsp.highpass(fs, p.hp, 2)] + dsp.eq_chain(fs, p.eq))
    y = (y * dsp.undb(WORK_LUFS - dsp.integrated_lufs(y, fs))).astype(np.float32)
    y, gr = dsp.compressor(y, fs, p.comp_thr, p.comp_ratio, p.attack_ms, p.release_ms, knee_db=6.0)
    y = dsp.saturate(y, p.saturation)
    y = (y * dsp.undb(l_in - dsp.integrated_lufs(y, fs))).astype(np.float32)
    eq = ", ".join(f"{f:g} Hz {g:+.1f}" for _k, f, g, _q in p.eq)
    L.log(f"{name}: mastering '{key}': EQ [{eq}], kompresja {p.comp_ratio:g}:1 (redukcja do {gr:.1f} dB)",
          tag="master")
    return y, gr
