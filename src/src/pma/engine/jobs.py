"""Zadania wysokiego poziomu w osobnych procesach (GUI się nie zacina)."""
import multiprocessing as mp
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

from . import normalize as N
from .. import log as L
from ..i18n import count


def workers():
    return max(1, min(4, (os.cpu_count() or 2) - 1))


def pool():
    """Pula procesów + kolejka logów do mini-terminala (ex.log_queue)."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    ex = ProcessPoolExecutor(max_workers=workers(), mp_context=ctx, initializer=L.init_worker, initargs=(q,))
    ex.log_queue = q
    return ex


def warm():
    """Rozgrzewka procesu roboczego (import numpy/scipy) podczas ekranu startowego."""
    from . import vocal  # noqa: F401
    L.log("proces roboczy gotowy (numpy, scipy)", tag="worker")
    return True


def clean_title(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"^\s*\d{1,3}\s*[-._)]*\s*", "", stem) or stem


# ------------------------------------------------------------------ album
def normalize_album(ex, infos, target, mode, out_dir, formats, wav_quality, cover, meta, on_progress=None,
                    master_key="off", manual=None):
    ok = [i for i in infos if not i.error]
    pl = N.plan(ok, target, mode, manual)
    ceil = N.ceiling(target, manual)
    L.log(f"normalizacja: {count(len(ok), 'song', 'pl')}, cel {N.target_value(target, manual):+.1f} LUFS, tryb {mode}, "
          f"pułap {ceil:.1f} dBTP, mastering {master_key}", tag="album")
    results = [None] * len(ok)
    futs = [ex.submit(N._job, n, i.path, *pl[i.path], out_dir, tuple(formats), wav_quality, cover, meta,
                      len(ok), clean_title(i.path), master_key, ceil) for n, i in enumerate(ok)]
    done = 0
    for f in as_completed(futs):
        idx, st, files = f.result()
        results[idx] = dict(info=ok[idx], stats=st, files=files)
        done += 1
        if on_progress:
            on_progress(idx, done, len(ok))
    return results


def squashed(results):
    """Numery utworów (od 1), w których limiter ściął szczyty o więcej niż N.SQUASH_WARN_DB."""
    return [n for n, r in enumerate(results, 1) if r["stats"]["limited"] > N.SQUASH_WARN_DB]


def report_text(results, tr, target, mode, master_key="off", manual=None):
    ceil = N.ceiling(target, manual)
    tname = tr("target_manual", lufs=N.target_value(target, manual)) if target == "manual" else tr("target_" + target)
    lines = [tr("report_title"), "=" * 104,
             tr("report_target", target=tname, mode=tr("mode_" + mode), ceil=ceil),
             tr("report_master", name=tr("mp_" + master_key)), ""]
    lines.append(f"{'#':>2}  {tr('col_track'):30s} {tr('col_before'):>16s} {tr('col_after'):>16s}   "
                 f"{tr('col_chorus'):>13s}  {'LRA':>9s}  {tr('col_limiter'):>8s}")
    for n, r in enumerate(results, 1):
        i, st = r["info"], r["stats"]
        before = f"{i.lufs:6.1f} / {i.true_peak:5.1f}"
        after = f"{st['lufs']:6.1f} / {st['true_peak']:5.1f}"
        chorus = f"{i.loud:5.1f} > {st['loud']:5.1f}"
        lra = f"{i.lra:4.1f} > {st['lra']:4.1f}"
        lim = f"{st['limited']:4.1f} dB" + (" !" if st["limited"] > N.SQUASH_WARN_DB else "  ")
        lines.append(f"{n:>2}  {os.path.basename(i.path)[:30]:30s} {before:>16s} {after:>16s}   {chorus:>13s}  "
                     f"{lra:>9s}  {lim:>8s}")
        for fmt, f in r["files"].items():
            ok = f["true_peak"] is not None and f["true_peak"] <= ceil + 0.01
            lines.append(f"      {fmt.upper():4s} true peak {f['true_peak']:6.2f} dBTP  {'OK' if ok else '!!'}")
    sq = squashed(results)
    if sq:
        lines += ["", tr("report_squash", tracks=", ".join(f"{n:02d}" for n in sq), db=N.SQUASH_WARN_DB)]
    lines += ["", tr("report_units"), tr("report_chorus"), tr("report_lra"), tr("report_limiter")]
    return "\n".join(lines)


# ------------------------------------------------------------------ odsłuch A/B: krzywe głośności
def loudness_curves(path):
    """Głośność chwilowa (400 ms) i krótkookresowa (3 s) co 100 ms + zintegrowana – liczona raz,
    a w trakcie odsłuchu tylko odczytywana dla bieżącej pozycji (dokładnie wg EBU R128)."""
    from . import dsp
    from .common import load
    from .export import _decode
    try:
        x, fs = load(path)
    except Exception:  # noqa: BLE001  (MP3 / MP4 – dekodowanie przez ffmpeg)
        x, fs = _decode(path), 44100
    mom = dsp._lufs_from_power(dsp._block_powers(x, fs, 0.4, 0.1))
    st = dsp.short_term(x, fs, 0.1)
    return dict(momentary=mom.astype("float32"), short=st.astype("float32"),
                integrated=dsp.integrated_lufs(x, fs), hop=0.1)


# ------------------------------------------------------------------ próbka masteringu (zakładka Album)
PREVIEW_DIR = os.path.join(os.path.expanduser("~/.cache"), "linux-project-mastering-audio", "preview")


def preview_excerpt(path, master_key, gain_db, ceil, seconds=20.0):
    """Najgłośniejsze `seconds` s utworu: oryginał (A) i ten sam fragment po masteringu, z tym samym
    wzmocnieniem co cały utwór dostałby przy normalizacji, i z limiterem do pułapu (B)."""
    import hashlib
    import numpy as np
    import soundfile as sf
    from . import dsp, master
    from .common import load
    key = hashlib.sha1(f"{path}|{os.path.getmtime(path)}|{master_key}|{gain_db:.2f}|{ceil}|{seconds}|v1"
                       .encode()).hexdigest()[:16]
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    pa, pb = (os.path.join(PREVIEW_DIR, f"{key}_{s}.wav") for s in ("a", "b"))
    x, fs = load(path)
    n = int(seconds * fs)
    start = 0
    if len(x) > n:
        st = dsp.short_term(x, fs, 0.5)                    # okna 3 s co 0,5 s
        k = max(1, int((seconds - 3) / 0.5))
        p = 10 ** (st / 10)
        avg = np.convolve(p, np.ones(k) / k, mode="valid") if len(p) >= k else p
        start = min(int(np.argmax(avg) * 0.5 * fs), len(x) - n)
    seg = x[start:start + n]
    if not (os.path.exists(pa) and os.path.exists(pb)):
        y, _gr = master.process(seg, fs, master_key, os.path.basename(path))
        y = (y * dsp.undb(gain_db)).astype(np.float32)
        if dsp.true_peak_db(y) > ceil:
            y, _ = N._protect(y, fs, ceil)
        sf.write(pa + ".tmp.wav", seg, fs, subtype="FLOAT")
        sf.write(pb + ".tmp.wav", y, fs, subtype="FLOAT")
        os.replace(pa + ".tmp.wav", pa)
        os.replace(pb + ".tmp.wav", pb)
    L.log(f"próbka {os.path.basename(path)}: {start / fs:.0f}–{(start + n) / fs:.0f} s, mastering {master_key}, "
          f"wzmocnienie {gain_db:+.1f} dB", tag="preview")
    yb, _ = sf.read(pb, dtype="float32", always_2d=True)
    return dict(a=pa, b=pb, a_lufs=dsp.integrated_lufs(seg, fs), b_lufs=dsp.integrated_lufs(yb, fs),
                start=start / fs)
