"""Podstawowe bloki DSP: filtry, pomiar głośności (ITU-R BS.1770-4), true peak,
kompresor, nasycenie, soft-clip i limiter true-peak.

Sygnał zawsze ma kształt (próbki, kanały) i typ float32/float64.
"""
import math
import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d


def db(x):
    return 20.0 * math.log10(max(float(x), 1e-12))


def undb(d):
    return 10.0 ** (d / 20.0)


def as2d(x):
    x = np.asarray(x)
    return x[:, None] if x.ndim == 1 else x


# ---------------------------------------------------------------- filtry (RBJ)
def _biquad(b, a):
    b = np.asarray(b, dtype=np.float64) / a[0]
    a = np.asarray(a, dtype=np.float64) / a[0]
    return np.concatenate([b, a])[None, :]


def peaking(fs, f0, gain_db, q=1.0):
    A = 10 ** (gain_db / 40)
    w = 2 * math.pi * f0 / fs
    al = math.sin(w) / (2 * q)
    c = math.cos(w)
    return _biquad([1 + al * A, -2 * c, 1 - al * A], [1 + al / A, -2 * c, 1 - al / A])


def shelf(fs, f0, gain_db, high, q=0.707):
    A = 10 ** (gain_db / 40)
    w = 2 * math.pi * f0 / fs
    c, s = math.cos(w), math.sin(w)
    al = s / (2 * q)
    sa = 2 * math.sqrt(A) * al
    if high:
        b = [A * ((A + 1) + (A - 1) * c + sa), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sa)]
        a = [(A + 1) - (A - 1) * c + sa, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sa]
    else:
        b = [A * ((A + 1) - (A - 1) * c + sa), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sa)]
        a = [(A + 1) + (A - 1) * c + sa, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sa]
    return _biquad(b, a)


def highpass(fs, f0, order=2):
    return signal.butter(order, f0, btype="highpass", fs=fs, output="sos")


def apply_sos(x, sos_list):
    if not sos_list:
        return x
    sos = np.concatenate(sos_list, axis=0)
    return signal.sosfilt(sos, x, axis=0).astype(x.dtype, copy=False)


def eq_chain(fs, bands):
    """bands: lista krotek (typ, f0, gain_db, q). typ: 'peak' | 'low' | 'high'."""
    out = []
    for kind, f0, g, q in bands:
        if abs(g) < 0.05 or f0 >= fs / 2 * 0.95:
            continue
        if kind == "peak":
            out.append(peaking(fs, f0, g, q))
        else:
            out.append(shelf(fs, f0, g, kind == "high", q))
    return out


# ------------------------------------------------------- głośność BS.1770-4
def _k_weighting(fs):
    """Filtr K (BS.1770) liczony dla dowolnej częstotliwości – przy 48 kHz daje
    dokładnie współczynniki z normy."""
    G, Q, fc = 3.999843853973347, 0.7071752369554193, 1681.974450955533
    K = math.tan(math.pi * fc / fs)
    Vh = 10 ** (G / 20)
    Vb = Vh ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    s1 = _biquad([(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0],
                 [1.0, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0])
    Q2, fc2 = 0.5003270373253953, 38.13547087613982
    K = math.tan(math.pi * fc2 / fs)
    a0 = 1 + K / Q2 + K * K
    s2 = _biquad([1.0, -2.0, 1.0], [1.0, 2 * (K * K - 1) / a0, (1 - K / Q2 + K * K) / a0])
    return np.concatenate([s1, s2], axis=0)


def _block_powers(x, fs, block_s, hop_s):
    x = as2d(x)
    y = signal.sosfilt(_k_weighting(fs), x.astype(np.float64), axis=0)
    cs = np.vstack([np.zeros((1, y.shape[1])), np.cumsum(y * y, axis=0)])
    n = int(round(block_s * fs))
    h = int(round(hop_s * fs))
    if len(y) < n:
        return np.array([np.sum(cs[-1] / max(len(y), 1))])
    starts = np.arange(0, len(y) - n + 1, h)
    z = (cs[starts + n] - cs[starts]) / n          # (bloki, kanały)
    return z.sum(axis=1)                            # wagi kanałów L/R = 1.0


def _lufs_from_power(p):
    return -0.691 + 10 * np.log10(np.maximum(p, 1e-20))


def integrated_lufs(x, fs):
    p = _block_powers(x, fs, 0.4, 0.1)
    l = _lufs_from_power(p)
    p = p[l > -70]
    if p.size == 0:
        return -70.0
    rel = _lufs_from_power(p.mean()) - 10
    p2 = p[_lufs_from_power(p) > rel]
    return float(_lufs_from_power(p2.mean())) if p2.size else -70.0


def short_term(x, fs, hop_s=0.5):
    """Głośność krótkookresowa (okno 3 s) co hop_s sekund."""
    return _lufs_from_power(_block_powers(x, fs, 3.0, hop_s))


def loudness_range(x, fs):
    st = short_term(x, fs, 0.1)
    st = st[st > -70]
    if st.size < 2:
        return 0.0
    rel = _lufs_from_power(np.mean(10 ** ((st + 0.691) / 10))) - 20
    st = st[st > rel]
    if st.size < 2:
        return 0.0
    return float(np.percentile(st, 95) - np.percentile(st, 10))


# ------------------------------------------------------------- nadpróbkowanie
def _chunked_envelope(x, factor, chunk=1 << 17, pad=128):
    """max |x| po nadpróbkowaniu `factor` razy, liczone kawałkami (oszczędza RAM)."""
    x = as2d(x)
    n = len(x)
    out = np.empty(n, dtype=np.float32)
    for s in range(0, n, chunk):
        a, b = max(0, s - pad), min(n, s + chunk + pad)
        up = signal.resample_poly(x[a:b].astype(np.float64), factor, 1, axis=0)
        e = min(chunk, n - s)
        seg = np.abs(up[(s - a) * factor:(s - a + e) * factor]).max(axis=1)
        out[s:s + e] = seg.reshape(e, factor).max(axis=1)
    return np.maximum(out, np.abs(x).max(axis=1))


def tp_envelope(x, fs=None, factor=4):
    """Obwiednia true peak (max |sygnału| po 4x nadpróbkowaniu, maks. po kanałach)."""
    return _chunked_envelope(x, factor)


def true_peak_db(x):
    env = tp_envelope(x)
    return db(float(env.max())) if env.size else -120.0


def oversampled_map(x, func, factor=2, chunk=1 << 17, pad=256):
    """Nieliniowa funkcja punktowa liczona w nadpróbkowaniu (mniej aliasingu)."""
    x = as2d(x)
    n = len(x)
    out = np.empty_like(x)
    for s in range(0, n, chunk):
        a, b = max(0, s - pad), min(n, s + chunk + pad)
        up = signal.resample_poly(x[a:b].astype(np.float64), factor, 1, axis=0)
        dn = signal.resample_poly(func(up), 1, factor, axis=0)
        e = min(chunk, n - s)
        out[s:s + e] = dn[s - a:s - a + e]
    return out


# ---------------------------------------------------------------- dynamika
def compressor(x, fs, thr_db, ratio, attack_ms, release_ms, knee_db=8.0):
    if ratio <= 1.0:
        return x, 0.0
    blk = max(16, int(fs * 0.002))
    n = len(x)
    nb = (n + blk - 1) // blk
    xp = np.zeros((nb * blk, x.shape[1]), dtype=np.float64)
    xp[:n] = x
    ms = (xp.reshape(nb, blk, -1) ** 2).mean(axis=1).max(axis=1)
    lvl = 10 * np.log10(np.maximum(ms, 1e-12)) + 3.01      # RMS sinusa -> szczyt
    over = lvl - thr_db
    slope = 1.0 / ratio - 1.0
    gr = np.where(over <= -knee_db / 2, 0.0,
                  np.where(over >= knee_db / 2, slope * over,
                           slope * (over + knee_db / 2) ** 2 / (2 * knee_db)))
    t = blk / fs
    aa = math.exp(-t / (attack_ms / 1000))
    ar = math.exp(-t / (release_ms / 1000))
    sm = np.empty_like(gr)
    g = 0.0
    for i, v in enumerate(gr.tolist()):
        g = aa * g + (1 - aa) * v if v < g else ar * g + (1 - ar) * v
        sm[i] = g
    centers = np.arange(nb) * blk + blk / 2
    gs = np.interp(np.arange(n), centers, sm)
    y = (x * (10 ** (gs / 20))[:, None]).astype(x.dtype)
    return y, float(-np.percentile(sm, 95))


def saturate(x, amount):
    """Delikatne nasycenie (harmoniczne + łagodne zaokrąglenie szczytów)."""
    if amount <= 0:
        return x
    k = 1.6

    def f(u):
        return u + amount * (np.tanh(u * k) / k - u)
    return oversampled_map(x, f, 2)


def soft_clip(x, ceiling_db=-0.3, knee=0.75):
    """Miękki clipper przed limiterem – ścina pojedyncze transjenty bez pompowania."""
    c = undb(ceiling_db)
    t = c * knee

    def f(u):
        a = np.abs(u)
        over = a > t
        y = u.copy()
        y[over] = np.sign(u[over]) * (t + (c - t) * np.tanh((a[over] - t) / (c - t)))
        return y
    return oversampled_map(x, f, 2)


def limiter(x, fs, ceiling_db=-1.0, lookahead_ms=2.5, release_ms=80.0):
    """Limiter true-peak z wyprzedzeniem (offline, wycentrowane okna)."""
    c = undb(ceiling_db)
    env = tp_envelope(x)
    g_req = np.minimum(1.0, c / np.maximum(env, 1e-9))
    if g_req.min() >= 1.0:
        return x, 0.0
    L = max(1, int(fs * lookahead_ms / 1000))
    g1 = minimum_filter1d(g_req, size=2 * L + 1, mode="nearest")
    g2 = uniform_filter1d(g1, size=2 * L + 1, mode="nearest")
    # wolniejszy powrót (release) liczony blokowo, zawsze <= g2
    blk = 32
    n = len(g2)
    nb = (n + blk - 1) // blk
    gp = np.ones(nb * blk)
    gp[:n] = g2
    bmin = gp.reshape(nb, blk).min(axis=1)
    rc = 1 - math.exp(-blk / (fs * release_ms / 1000))
    rel = np.empty(nb)
    g = 1.0
    for i, v in enumerate(bmin.tolist()):
        g = v if v < g else g + (v - g) * rc
        rel[i] = g
    gs = np.minimum(g2, np.interp(np.arange(n), np.arange(nb) * blk + blk / 2, rel))
    y = (x * gs[:, None]).astype(x.dtype)
    return y, float(-db(gs.min()))
