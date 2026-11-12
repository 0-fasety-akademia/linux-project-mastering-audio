"""Mikser na żywo (GStreamer audiomixer): każda ścieżka = sucha + efekt,
głośność i pogłos zmieniane w trakcie odtwarzania, miernik szczytu."""
import os
import re

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

from ..engine.vocal import fx_gain  # noqa: E402
from .. import log as L  # noqa: E402

Gst.init(None)


def _q(path):
    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


class LiveMixer:
    def __init__(self, on_state=None, on_level=None):
        self.pipe = None
        self.tracks = []          # dict(dry, wet, volume_db, fx, mute)
        self.playing = False
        self.on_state = on_state
        self.on_level = on_level
        self._dur = 0.0

    # ------------------------------------------------------------ budowa
    def set_tracks(self, tracks):
        """tracks: lista obiektów z polami dry, wet, volume_db, fx, mute (dry/wet mogą być None)."""
        pos, was = self.position(), self.playing
        self._teardown()
        self.tracks = [t for t in tracks if t.dry and t.wet]
        if not self.tracks:
            self._notify()
            return
        sink = "fakesink sync=true" if os.environ.get("PMA_FAKESINK") else "autoaudiosink"
        parts = [f"audiomixer name=mix ! audioconvert ! audio/x-raw,format=F32LE ! "
                 f"level name=lvl interval=60000000 post-messages=true ! audioconvert ! {sink}"]
        for i, t in enumerate(self.tracks):
            for kind in ("dry", "wet"):
                parts.append(f"filesrc location={_q(getattr(t, kind))} ! wavparse ! audioconvert ! "
                             f"audioresample ! volume name={kind}{i} ! mix.")
        self.pipe = Gst.parse_launch("  ".join(parts))
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self._eos)
        bus.connect("message::error", self._err)
        bus.connect("message::element", self._element)
        self.update_volumes()
        self.pipe.set_state(Gst.State.PAUSED)
        self.pipe.get_state(3 * Gst.SECOND)
        self._dur = 0.0
        if pos > 0:
            self.seek(pos)
        if was:
            self.play()
        self._notify()

    def update_volumes(self):
        if not self.pipe:
            return
        for i, t in enumerate(self.tracks):
            v = 0.0 if t.mute else 10 ** (t.volume_db / 20)
            self.pipe.get_by_name(f"dry{i}").set_property("volume", min(v, 10.0))
            self.pipe.get_by_name(f"wet{i}").set_property("volume", min(v * fx_gain(t.fx), 10.0))

    def _teardown(self):
        if self.pipe:
            self.pipe.set_state(Gst.State.NULL)
            self.pipe.get_bus().remove_signal_watch()
            self.pipe = None
        self.playing = False

    # ------------------------------------------------------------ sterowanie
    def play(self):
        if self.pipe and not self.playing:
            L.log("odtwarzanie ▶", tag="mixer")
        if self.pipe:
            self.pipe.set_state(Gst.State.PLAYING)
            self.playing = True
            self._notify()

    def pause(self):
        if self.pipe:
            self.pipe.set_state(Gst.State.PAUSED)
        self.playing = False
        self._notify()

    def toggle(self):
        self.pause() if self.playing else self.play()

    def stop(self):
        self._teardown()
        self._notify()

    def position(self):
        if not self.pipe:
            return 0.0
        ok, p = self.pipe.query_position(Gst.Format.TIME)
        return p / Gst.SECOND if ok else 0.0

    def duration(self):
        if not self.pipe:
            return 0.0
        if self._dur <= 0:
            ok, d = self.pipe.query_duration(Gst.Format.TIME)
            self._dur = d / Gst.SECOND if ok and d > 0 else 0.0
        return self._dur

    def seek(self, sec):
        if self.pipe:
            self.pipe.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
                                  int(max(0.0, sec) * Gst.SECOND))

    # ------------------------------------------------------------ bus
    def _eos(self, *_):
        def back():
            self.pause()
            self.seek(0)
            return False
        GLib.idle_add(back)

    def _err(self, _bus, msg):
        err, _ = msg.parse_error()
        print("GStreamer:", err.message)
        self._teardown()
        self._notify()

    def _element(self, _bus, msg):
        s = msg.get_structure()
        if s and s.get_name() == "level" and self.on_level:
            m = re.search(r"peak=\([^)]*\)[{<]([^}>]*)[}>]", s.to_string())
            if m:
                vals = [float(v) for v in m.group(1).split(",") if v.strip()]
                self.on_level(max(vals) if vals else -90.0)

    def _notify(self):
        if self.on_state:
            self.on_state()
