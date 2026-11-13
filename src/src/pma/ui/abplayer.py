"""Odsłuch A/B: oryginał i wynik grają RÓWNOCZEŚNIE i zsynchronizowane (audiomixer),
przełącznik tylko zmienia, która ścieżka jest słyszalna – bez przeskoku w czasie.
Obie wersje są wyrównane do tej samej głośności (ciszej grająca nigdy nie jest podbijana)."""
import os

from gi.repository import Gst

from ..engine.dsp import undb
from .. import log as L
from .mixer import LiveMixer, _q

CAPS = "audio/x-raw,format=F32LE,channels=2,rate=48000"


class ABPlayer(LiveMixer):
    def __init__(self, on_state=None):
        super().__init__(on_state=on_state)
        self.side = "b"
        self.gains = (1.0, 1.0)
        self.paths = None

    @staticmethod
    def matched_gains(lufs_a, lufs_b):
        """(gain_a_db, gain_b_db, wspólny poziom): głośniejszą wersję ściszamy do cichszej."""
        ref = min(lufs_a, lufs_b)
        return ref - lufs_a, ref - lufs_b, ref

    def load(self, path_a, path_b, gain_a_db, gain_b_db):
        was = self.playing
        self._teardown()
        self.paths = (path_a, path_b)
        self.gains = (undb(gain_a_db), undb(gain_b_db))
        sink = "fakesink sync=true" if os.environ.get("PMA_FAKESINK") else "autoaudiosink"
        parts = [f"audiomixer name=mix ! audioconvert ! audioresample ! {sink}"]
        for name, p in (("va", path_a), ("vb", path_b)):
            parts.append(f"filesrc location={_q(p)} ! decodebin ! audioconvert ! audioresample ! {CAPS} ! "
                         f"volume name={name} ! mix.")
        self.pipe = Gst.parse_launch("  ".join(parts))
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self._eos)
        bus.connect("message::error", self._err)
        self.update_volumes()
        self.pipe.set_state(Gst.State.PAUSED)
        self.pipe.get_state(3 * Gst.SECOND)
        self._dur = 0.0
        L.log(f"A/B: {os.path.basename(path_a)} ↔ {os.path.basename(path_b)} "
              f"(A {gain_a_db:+.1f} dB, B {gain_b_db:+.1f} dB)", tag="ab")
        if was:
            self.play()
        self._notify()

    def set_side(self, side):
        self.side = side
        self.update_volumes()

    def update_volumes(self):
        if not self.pipe:
            return
        self.pipe.get_by_name("va").set_property("volume", self.gains[0] if self.side == "a" else 0.0)
        self.pipe.get_by_name("vb").set_property("volume", self.gains[1] if self.side == "b" else 0.0)
