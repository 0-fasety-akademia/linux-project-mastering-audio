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
def normalize_album(ex, infos, target, mode, out_dir, formats, wav_quality, cover, meta, on_progress=None):
    ok = [i for i in infos if not i.error]
    pl = N.plan(ok, target, mode)
    L.log(f"normalizacja: {count(len(ok), 'song', 'pl')}, cel {N.TARGETS[target]:+.1f} LUFS, tryb {mode}", tag="album")
    results = [None] * len(ok)
    futs = [ex.submit(N._job, n, i.path, *pl[i.path], out_dir, tuple(formats), wav_quality, cover, meta,
                      len(ok), clean_title(i.path)) for n, i in enumerate(ok)]
    done = 0
    for f in as_completed(futs):
        idx, st, files = f.result()
        results[idx] = dict(info=ok[idx], stats=st, files=files)
        done += 1
        if on_progress:
            on_progress(idx, done, len(ok))
    return results


def report_text(results, tr, target, mode):
    lines = [tr("report_title"), "=" * 90,
             tr("report_target", target=tr("target_" + target), mode=tr("mode_" + mode)), ""]
    lines.append(f"{'#':>2}  {tr('col_track'):30s} {tr('col_before'):>16s} {tr('col_after'):>16s}   "
                 f"{tr('col_chorus'):>13s}")
    for n, r in enumerate(results, 1):
        i, st = r["info"], r["stats"]
        before = f"{i.lufs:6.1f} / {i.true_peak:5.1f}"
        after = f"{st['lufs']:6.1f} / {st['true_peak']:5.1f}"
        chorus = f"{i.loud:5.1f} > {st['loud']:5.1f}"
        lines.append(f"{n:>2}  {os.path.basename(i.path)[:30]:30s} {before:>16s} {after:>16s}   {chorus:>13s}")
        for fmt, f in r["files"].items():
            ok = f["true_peak"] is not None and f["true_peak"] <= N.CEILING_DBTP + 0.01
            lines.append(f"      {fmt.upper():4s} true peak {f['true_peak']:6.2f} dBTP  {'OK' if ok else '!!'}")
    lines += ["", tr("report_units"), tr("report_chorus")]
    return "\n".join(lines)
