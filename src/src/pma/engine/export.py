"""Zapis: WAV (CD 16-bit/44.1 kHz z ditherem lub 24-bit), MP3 320 kbps, MP4 (AAC 256 kbps)
z okładką i tagami. Pliki stratne są sprawdzane PO zakodowaniu – jeśli kodek dodał
przester (true peak ponad pułap, zwykle −1 dBTP), poziom jest korygowany i plik kodowany ponownie."""
import os
import shutil
import subprocess
import tempfile

import numpy as np
import soundfile as sf

from . import dsp
from .. import log as L
from .common import CEILING_DBTP, safety_limit, to_rate

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FDKAAC = shutil.which("fdkaac")   # Fraunhofer FDK AAC – dużo czystszy niż wbudowany koder ffmpeg


def tpdf_16(x, seed=0):
    rng = np.random.default_rng(seed)
    lsb = 1.0 / 32768.0
    d = (rng.random(x.shape) - rng.random(x.shape)) * lsb
    return np.clip(np.round((x + d) * 32767.0), -32768, 32767).astype(np.int16)


def write_wav(path, x, fs, quality, tags, ceiling=CEILING_DBTP):
    if quality == "cd":
        y = safety_limit(to_rate(x, fs, 44100), 44100, ceiling)
        data, rate, sub = tpdf_16(y), 44100, "PCM_16"
    else:
        data, rate, sub = x, fs, "PCM_24"
    with sf.SoundFile(path, "w", rate, data.shape[1], subtype=sub, format="WAV") as f:
        for k in ("title", "artist", "album", "tracknumber"):
            if tags.get(k):
                try:
                    setattr(f, k, str(tags[k]))
                except Exception:  # noqa: BLE001
                    pass
        f.write(data)
    return dict(path=path, true_peak=dsp.true_peak_db(data.astype(np.float32) / (32768.0 if sub == "PCM_16" else 1.0)))


def _decode(path):
    p = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-map", "0:a:0", "-f", "f32le", "-ac", "2", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, 2)


def _encode(fmt, wav_path, out_path, cover, tags):
    src_codec = []
    if fmt == "mp4" and FDKAAC:
        m4a = wav_path + ".m4a"
        subprocess.run([FDKAAC, "-S", "-b", "256", "-o", m4a, wav_path], check=True, capture_output=True)
        wav_path, src_codec = m4a, ["-c:a", "copy"]
    cmd = [FFMPEG, "-v", "error", "-y", "-i", wav_path]
    has_cover = bool(cover and os.path.exists(cover))
    if has_cover:
        cmd += ["-i", cover]
    cmd += ["-map", "0:a"]
    if has_cover:
        cmd += ["-map", "1:v"]
    if fmt == "mp3":
        cmd += ["-c:a", "libmp3lame", "-b:a", "320k", "-ar", "44100", "-id3v2_version", "3"]
        if has_cover:
            cmd += ["-c:v", "png", "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
    else:
        cmd += (src_codec or ["-c:a", "aac", "-b:a", "256k", "-ar", "44100"]) + ["-movflags", "+faststart"]
        if has_cover:
            cmd += ["-c:v", "png", "-disposition:v:0", "attached_pic"]
    names = {"title": "title", "artist": "artist", "album": "album", "tracknumber": "track"}
    for k, v in names.items():
        if tags.get(k):
            cmd += ["-metadata", f"{v}={tags[k]}"]
    cmd.append(out_path)
    subprocess.run(cmd, check=True, capture_output=True)


def write_lossy(fmt, path, x, fs, cover, tags, tmpdir, ceiling=CEILING_DBTP):
    """Koduje, dekoduje, mierzy true peak; w razie przesteru ścisza i koduje ponownie."""
    y = safety_limit(to_rate(x, fs, 44100), 44100, ceiling)
    trim = 0.0
    tp = None
    for _ in range(4):
        z = (y * dsp.undb(trim)).astype(np.float32)
        wav = os.path.join(tmpdir, "enc.wav")
        sf.write(wav, z, 44100, subtype="FLOAT")
        _encode(fmt, wav, path, cover, tags)
        tp = dsp.true_peak_db(_decode(path))
        if tp <= ceiling:
            break
        L.log(f"{os.path.basename(path)}: po kodowaniu {tp:+.2f} dBTP – ściszam i koduję ponownie", "warn",
              tag=fmt)
        trim -= (tp - ceiling) + 0.1
    return dict(path=path, true_peak=tp, trim=trim)


def export_track(x, fs, out_dir, stem, formats, wav_quality, cover, tags, ceiling=CEILING_DBTP):
    os.makedirs(out_dir, exist_ok=True)
    results = {}
    with tempfile.TemporaryDirectory(prefix="pma-") as tmp:
        if "wav" in formats:
            results["wav"] = write_wav(os.path.join(out_dir, stem + ".wav"), x, fs, wav_quality, tags, ceiling)
        if "mp3" in formats:
            results["mp3"] = write_lossy("mp3", os.path.join(out_dir, stem + ".mp3"), x, fs, cover, tags, tmp, ceiling)
        if "mp4" in formats:
            results["mp4"] = write_lossy("mp4", os.path.join(out_dir, stem + ".mp4"), x, fs, cover, tags, tmp, ceiling)
    return results
