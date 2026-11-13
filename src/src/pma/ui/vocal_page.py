"""Zakładka WOKAL: 1–10 ścieżek, 5 opcji masteringu, suwaki głośności i pogłosu/echa
działające na żywo, przycisk SCAL WSZYSTKIE ŚCIEŻKI W JEDNĄ."""
import os
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango  # noqa: E402

import soundfile as sf  # noqa: E402

from ..engine import vocal as V  # noqa: E402
from ..i18n import count, num, plural, tr  # noqa: E402
from . import common as C  # noqa: E402
from .. import log as L  # noqa: E402
from .mixer import LiveMixer  # noqa: E402

MAX_TRACKS = 10
LETTERS = "ABCDEFGHIJ"


class VTrack:
    def __init__(self, path, preset):
        self.path = path
        self.preset = preset
        self.volume_db = 0.0
        self.fx = V.PRESETS[preset].fx_default
        self.mute = False
        self.dry = self.wet = None
        self.duration = 0.0
        self.token = 0
        self.error = ""
        self.w = {}


class VocalPage(Gtk.Box):
    def __init__(self, win, executor):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.ex = executor
        self.tracks = []
        self.fs = None
        self.album_preset = "studio"
        self.busy = False
        self.peak_hold = (-90.0, 0.0)
        self.mixer = LiveMixer(on_state=self._sync_play, on_level=self._on_level)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, vexpand=True)
        self.stack.add_named(C.empty_page(tr("v_drop_title"), tr("v_drop_sub"), self.choose_files), "empty")
        self.stack.add_named(self._main(), "main")
        self.append(self.stack)
        self.bottom, self.status, self.progress, self.merge_btn = C.bottom_bar(tr("merge"), self.start_merge)
        self.player_bar = self._player_bar()
        self.append(Gtk.Separator())
        self.append(self.player_bar)
        self.append(self.bottom)

        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", lambda _t, v, *_: (self.add_files(C.collect_audio(v.get_files())[0]), True)[1])
        self.add_controller(drop)
        GLib.timeout_add(150, self._tick)
        self._update()

    # ================================================================ UI
    def _main(self):
        page = Adw.PreferencesPage()

        g = Adw.PreferencesGroup(title=tr("v_style"), description=tr("v_style_sub"))
        cards = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                            max_children_per_line=5, min_children_per_line=2, column_spacing=8, row_spacing=8)
        self.cards = {}
        first = None
        for key in V.PRESET_ORDER:
            b = Gtk.ToggleButton()
            b.add_css_class("preset-card")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            n = Gtk.Label(label=tr("vp_" + key), xalign=0)
            n.add_css_class("preset-name")
            d = Gtk.Label(label=tr(f"vp_{key}_d"), xalign=0, wrap=True, max_width_chars=18)
            d.add_css_class("preset-desc")
            box.append(n)
            box.append(d)
            b.set_child(box)
            if first:
                b.set_group(first)
            else:
                first = b
            b.connect("toggled", self._on_card, key)
            self.cards[key] = b
            cards.append(b)
        self.cards["studio"].set_active(True)
        g.add(cards)
        page.add(g)

        tg = Adw.PreferencesGroup(title=tr("v_tracks"))
        hb = Gtk.Box(spacing=4)
        for icon, tip, cb in (("list-add-symbolic", tr("add_files"), self.choose_files),
                              ("edit-clear-all-symbolic", tr("clear"), self.clear)):
            b = Gtk.Button(icon_name=icon, tooltip_text=tip, valign=Gtk.Align.CENTER)
            b.add_css_class("flat")
            b.connect("clicked", lambda *_, cb=cb: cb())
            hb.append(b)
        tg.set_header_suffix(hb)
        self.list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.list.add_css_class("boxed-list")
        tg.add(self.list)
        page.add(tg)

        return page

    def _player_bar(self):
        lg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for m in ("top", "bottom", "start", "end"):
            getattr(lg, f"set_margin_{m}")(8 if m in ("top", "bottom") else 18)
        row = Gtk.Box(spacing=10)
        self.play_btn = Gtk.Button(icon_name="media-playback-start-symbolic", tooltip_text=tr("play"),
                                   valign=Gtk.Align.CENTER)
        self.play_btn.add_css_class("circular")
        self.play_btn.add_css_class("suggested-action")
        self.play_btn.connect("clicked", lambda *_: self.mixer.toggle())
        self.pos = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        self.pos.set_hexpand(True)
        self.pos.set_draw_value(False)
        self._pos_h = self.pos.connect("change-value", lambda _s, _c, v: (self.mixer.seek(v), False)[1])
        self.time_lbl = Gtk.Label(label="0:00 / 0:00")
        self.time_lbl.add_css_class("numeric")
        row.append(self.play_btn)
        row.append(self.pos)
        row.append(self.time_lbl)
        lg.append(row)
        mrow = Gtk.Box(spacing=10)
        mrow.set_margin_top(8)
        self.meter = Gtk.LevelBar(min_value=0, max_value=1, hexpand=True, valign=Gtk.Align.CENTER)
        self.meter.add_css_class("peak-meter")
        self.meter.add_offset_value("hot", 0.95)
        self.meter_lbl = Gtk.Label(label="", xalign=0, ellipsize=Pango.EllipsizeMode.END, width_chars=10)
        self.meter_lbl.add_css_class("caption")
        mrow.append(self.meter)
        self.meter_db = Gtk.Label(label="−∞ dB", width_chars=8)
        self.meter_db.add_css_class("numeric")
        mrow.append(self.meter_db)
        lg.append(mrow)
        self.meter_msg = Gtk.Label(xalign=0, wrap=True)
        self.meter_msg.add_css_class("caption")
        self.meter_msg.set_margin_top(4)
        lg.append(self.meter_msg)
        return lg

    def _track_row(self, n, t):
        row = Gtk.ListBoxRow(activatable=False)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for m in ("top", "bottom"):
            getattr(outer, f"set_margin_{m}")(10)
        outer.set_margin_start(12)
        outer.set_margin_end(8)

        top = Gtk.Box(spacing=10)
        badge = Gtk.Label(label=LETTERS[n])
        badge.add_css_class("track-badge")
        badge.set_valign(Gtk.Align.CENTER)
        names = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, valign=Gtk.Align.CENTER)
        title = Gtk.Label(label=os.path.basename(t.path), xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE)
        title.add_css_class("heading")
        sub = Gtk.Label(xalign=0)
        sub.add_css_class("dim-label")
        sub.add_css_class("caption")
        names.append(title)
        names.append(sub)
        spin = Gtk.Spinner(valign=Gtk.Align.CENTER)
        dd = Gtk.DropDown.new_from_strings([tr("vp_" + k) for k in V.PRESET_ORDER])
        dd.set_selected(V.PRESET_ORDER.index(t.preset))
        dd.set_valign(Gtk.Align.CENTER)
        dd.connect("notify::selected", self._on_track_preset, t)
        mute = Gtk.ToggleButton(icon_name="audio-volume-muted-symbolic", tooltip_text=tr("mute"),
                                active=t.mute, valign=Gtk.Align.CENTER)
        mute.add_css_class("flat")
        mute.connect("toggled", self._on_mute, t)
        rm = Gtk.Button(icon_name="user-trash-symbolic", tooltip_text=tr("remove"), valign=Gtk.Align.CENTER)
        rm.add_css_class("flat")
        rm.connect("clicked", lambda *_: self.remove(t))
        for w in (badge, names, spin, dd, mute, rm):
            top.append(w)
        outer.append(top)

        sl = Gtk.Grid(column_spacing=10, row_spacing=2)
        sl.set_margin_start(38)
        vol_l = Gtk.Label(label=tr("volume"), xalign=0)
        vol_l.add_css_class("caption")
        vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -24, 12, 0.5)
        vol.set_value(t.volume_db)
        vol.set_hexpand(True)
        vol.set_draw_value(False)
        vol.add_mark(0, Gtk.PositionType.BOTTOM, None)
        vol_v = Gtk.Label(width_chars=8, xalign=1)
        vol_v.add_css_class("numeric")
        vol_v.add_css_class("caption")
        vol.connect("value-changed", self._on_volume, t)
        fx_l = Gtk.Label(label=tr("fx"), xalign=0)
        fx_l.add_css_class("caption")
        fx = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        fx.set_value(t.fx)
        fx.set_hexpand(True)
        fx.set_draw_value(False)
        fx_v = Gtk.Label(width_chars=8, xalign=1)
        fx_v.add_css_class("numeric")
        fx_v.add_css_class("caption")
        fx.connect("value-changed", self._on_fx, t)
        sl.attach(vol_l, 0, 0, 1, 1)
        sl.attach(vol, 1, 0, 1, 1)
        sl.attach(vol_v, 2, 0, 1, 1)
        sl.attach(fx_l, 0, 1, 1, 1)
        sl.attach(fx, 1, 1, 1, 1)
        sl.attach(fx_v, 2, 1, 1, 1)
        outer.append(sl)
        row.set_child(outer)
        t.w = dict(sub=sub, spin=spin, dd=dd, vol=vol, vol_v=vol_v, fx=fx, fx_v=fx_v, mute=mute)
        self._label_values(t)
        self._fill_sub(t)
        return row

    # ================================================================ pliki
    def choose_files(self):
        C.open_audio_dialog(self.win, self.add_files)

    def add_files(self, paths):
        if self.busy or not paths:
            return
        known = {t.path for t in self.tracks}
        paths = sorted([p for p in paths if p not in known], key=lambda p: os.path.basename(p).lower())
        room = MAX_TRACKS - len(self.tracks)
        if len(paths) > room:
            self.win.toast(f"Max {count(MAX_TRACKS, 'stem')}")
            paths = paths[:room]
        if not paths:
            return
        if self.fs is None:
            try:
                self.fs = sf.info(paths[0]).samplerate
            except Exception:  # noqa: BLE001
                self.fs = 48000
        new = [VTrack(p, self.album_preset) for p in paths]
        for p in paths:
            L.log(f"dodano ścieżkę {os.path.basename(p)}", tag="ui")
        self.tracks = sorted(self.tracks + new, key=lambda t: os.path.basename(t.path).lower())
        self._rebuild()
        for t in new:
            self._render(t)
        self._update()

    def remove(self, t):
        if self.busy:
            return
        self.tracks.remove(t)
        if not self.tracks:
            self.fs = None
        self._rebuild()
        self._remix()
        self._update()

    def clear(self):
        if self.busy:
            return
        self.tracks = []
        self.fs = None
        self.mixer.stop()
        self._rebuild()
        self._update()

    def _rebuild(self):
        self.list.remove_all()
        for n, t in enumerate(self.tracks):
            self.list.append(self._track_row(n, t))

    def _fill_sub(self, t):
        if not t.w:
            return
        rendering = t.dry is None and not t.error
        t.w["spin"].set_spinning(rendering)
        t.w["spin"].set_visible(rendering)
        if t.error:
            t.w["sub"].set_text(f"⚠ {tr('analysis_failed')}: {t.error[:70]}")
        elif rendering:
            t.w["sub"].set_text(tr("rendering"))
        else:
            t.w["sub"].set_text(f"{C.fmt_dur(t.duration)} · {tr('vp_' + t.preset)}")

    def _label_values(self, t):
        t.w["vol_v"].set_text(f"{num(t.volume_db, '+.1f')} dB")
        t.w["fx_v"].set_text(f"{int(round(t.fx))}%")

    # ================================================================ render
    def _render(self, t):
        t.token += 1
        tok = t.token
        t.dry = t.wet = None
        t.error = ""
        self._fill_sub(t)
        fut = self.ex.submit(V.render_track, t.path, t.preset, self.fs)
        fut.add_done_callback(lambda f: GLib.idle_add(self._rendered, t, tok, f))
        self._update()

    def _rendered(self, t, tok, fut):
        if tok != t.token or t not in self.tracks:
            return False
        try:
            t.dry, t.wet, t.duration = fut.result()
        except Exception as e:  # noqa: BLE001
            t.error = str(e)
        self._fill_sub(t)
        self._remix()
        self._update()
        return False

    def _remix(self):
        self.mixer.set_tracks(self.tracks)
        n = len([t for t in self.tracks if t.dry])
        if n:
            L.log(f"mikser GStreamer: {n} {plural(n, 'stem', 'pl')} × (sucha + efekt) -> audiomixer", tag="mixer")
        self._update()

    # ================================================================ zdarzenia
    def _on_card(self, btn, key):
        if not btn.get_active():
            return
        self.album_preset = key
        for t in self.tracks:
            if t.preset != key:
                t.w["dd"].set_selected(V.PRESET_ORDER.index(key))   # wywoła _on_track_preset

    def _on_track_preset(self, dd, _p, t):
        key = V.PRESET_ORDER[dd.get_selected()]
        if key == t.preset:
            return
        t.preset = key
        L.log(f"{os.path.basename(t.path)}: opcja -> {key}", tag="ui")
        t.fx = V.PRESETS[key].fx_default
        t.w["fx"].set_value(t.fx)
        self._render(t)

    def _on_volume(self, s, t):
        t.volume_db = round(s.get_value() * 2) / 2
        self._label_values(t)
        self.mixer.update_volumes()

    def _on_fx(self, s, t):
        t.fx = s.get_value()
        self._label_values(t)
        self.mixer.update_volumes()

    def _on_mute(self, b, t):
        t.mute = b.get_active()
        L.log(f"{os.path.basename(t.path)}: {'wyciszona' if t.mute else 'włączona'}", tag="ui")
        self.mixer.update_volumes()

    # ================================================================ odsłuch
    def _sync_play(self):
        p = self.mixer.playing
        self.play_btn.set_icon_name("media-playback-pause-symbolic" if p else "media-playback-start-symbolic")
        self.play_btn.set_tooltip_text(tr("pause") if p else tr("play"))

    def _on_level(self, db):
        now = time.monotonic()
        if db > self.peak_hold[0] or now - self.peak_hold[1] > 1.5:
            self.peak_hold = (db, now)
        self.meter.set_value(max(0.0, min(1.0, (db + 60) / 60)))
        self.meter_db.set_text(f"{num(db, '+.1f')} dB" if db > -90 else "−∞ dB")
        hot = self.peak_hold[0] > -1.0
        self.meter_msg.set_text(tr("meter_hot") if hot else tr("meter_ok"))
        self.meter_msg.remove_css_class("error" if not hot else "success")
        self.meter_msg.add_css_class("error" if hot else "success")

    def _tick(self):
        if self.mixer.pipe:
            self.mixer.check_stall()
            d = self.mixer.duration()
            pend = self.mixer.pending_position()
            p = pend if pend is not None else self.mixer.position()
            self.pos.handler_block(self._pos_h)
            self.pos.set_range(0, max(d, 0.1))
            self.pos.set_value(p)
            self.pos.handler_unblock(self._pos_h)
            self.time_lbl.set_text(f"{C.fmt_dur(p)} / {C.fmt_dur(d)}")
        if not self.mixer.playing:
            self.meter.set_value(0)
        return True

    # ================================================================ scalanie
    def _ready(self):
        return [t for t in self.tracks if t.dry and not t.error]

    def _update(self):
        self.stack.set_visible_child_name("main" if self.tracks else "empty")
        self.bottom.set_visible(bool(self.tracks))
        self.player_bar.set_visible(bool(self.tracks))
        rendering = any(t.dry is None and not t.error for t in self.tracks)
        ok = self._ready()
        self.merge_btn.set_sensitive(bool(ok) and not rendering and not self.busy)
        has = self.mixer.pipe is not None
        self.play_btn.set_sensitive(has)
        self.pos.set_sensitive(has)
        if not self.busy:
            if rendering:
                self.status.set_text(tr("rendering"))
            elif ok:
                self.status.set_text(tr("count_dur", count=count(len(ok), "stem"), dur=C.fmt_dur(max(t.duration for t in ok))))
            else:
                self.status.set_text("")

    def _default_name(self):
        stems = [os.path.splitext(os.path.basename(t.path))[0] for t in self.tracks]
        pre = os.path.commonprefix(stems).strip(" -_.") if len(stems) > 1 else stems[0]
        if len(pre) >= 3:
            return f"{pre} - {tr('merged_suffix')}.wav"
        return f"{tr('merged_suffix')}.wav"

    def start_merge(self):
        tracks = [t for t in self._ready() if not t.mute]
        if not tracks:
            return
        dlg = Gtk.FileDialog(title=tr("merge_save_title"), initial_name=self._default_name())
        dlg.set_initial_folder(Gio.File.new_for_path(os.path.dirname(tracks[0].path)))

        def done(d, res):
            try:
                out = d.save_finish(res).get_path()
            except GLib.Error:
                return
            if not out.lower().endswith(".wav"):
                out += ".wav"
            self._do_merge(tracks, out)
        dlg.save(self.win, None, done)

    def _do_merge(self, tracks, out):
        self.mixer.pause()
        for t in tracks:
            L.log(f"{os.path.basename(t.path)}: {t.preset}, głośność {t.volume_db:+.1f} dB, efekt {int(t.fx)}%",
                  tag="merge")
        self.busy = True
        self.progress.set_visible(True)
        self.progress.pulse()
        self.status.set_text(tr("merging"))
        self._update()
        spec = [dict(dry=t.dry, wet=t.wet, volume_db=t.volume_db, fx=t.fx) for t in tracks]
        fut = self.ex.submit(V.merge, spec, out, self.fs)
        pulse = GLib.timeout_add(120, lambda: (self.progress.pulse(), True)[1])
        fut.add_done_callback(lambda f: GLib.idle_add(self._merged, f, pulse))

    def _merged(self, fut, pulse):
        GLib.source_remove(pulse)
        self.busy = False
        self.progress.set_visible(False)
        self._update()
        try:
            r = fut.result()
        except Exception as e:  # noqa: BLE001
            d = Adw.AlertDialog(heading=tr("error"), body=str(e))
            d.add_response("close", tr("close"))
            d.present(self.win)
            return False
        body = tr("merge_done_body", name=os.path.basename(r["path"]), lufs=r["lufs"], tp=r["true_peak"])
        if r["limited_db"] > 0.05:
            body += tr("merge_limited", db=r["limited_db"])
        self.win.app.notify(tr("notif_merge"), os.path.basename(r["path"]))
        d = Adw.AlertDialog(heading=tr("merge_done_title"), body=body)
        d.add_response("close", tr("close"))
        d.add_response("open", tr("open_folder"))
        d.set_response_appearance("open", Adw.ResponseAppearance.SUGGESTED)
        d.connect("response", lambda _d, resp: resp == "open" and C.open_folder(self.win, os.path.dirname(r["path"])))
        d.present(self.win)
        return False
