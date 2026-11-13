"""Zakładka ALBUM: opcjonalny lekki mastering i normalizacja głośności gotowych utworów,
wykres płyty i odsłuch A/B z wyrównaną głośnością."""
import os
import threading
import traceback

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import i18n  # noqa: E402
from ..engine import jobs  # noqa: E402
from ..engine import master as M  # noqa: E402
from ..engine import normalize as N  # noqa: E402
from ..i18n import count, num, tr  # noqa: E402
from . import common as C  # noqa: E402
from .ab_meter import ABMeter  # noqa: E402
from .abplayer import ABPlayer  # noqa: E402
from .album_chart import AlbumChart  # noqa: E402
from .. import log as L  # noqa: E402


class ATrack:
    def __init__(self, path):
        self.path = path
        self.info = None
        self.row = None
        self.spin = None
        self.ok_icon = None


class AlbumPage(Gtk.Box):
    def __init__(self, win, executor):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.win = win
        self.ex = executor
        self.tracks = []
        self.cover = None
        self.busy = False
        self.results = None          # wyniki ostatniej normalizacji (lista dict info/stats/files)
        self.results_key = None      # ustawienia, z którymi powstały – wykres pokazuje je tylko gdy się zgadzają
        self.ab_meters = {"a": ABMeter(), "b": ABMeter()}      # dwa mierniki obok siebie: A i B
        self._ab_key = None        # ustawienia, z którymi załadowano odsłuch (wyniki albo próbka)
        self._ab_stale = False
        self.ab = ABPlayer(on_state=self._ab_sync, on_level=self._ab_peak)
        self._curves = {}          # ścieżka -> krzywe głośności (liczone raz w procesie roboczym)
        self._ab_cur = None        # (krzywe A, krzywe B, gain A dB, gain B dB) bieżącego utworu

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, vexpand=True)
        self.stack.add_named(C.empty_page(tr("a_drop_title"), tr("a_drop_sub"), self.choose_files), "empty")
        self.stack.add_named(self._main(), "main")
        self.append(self.stack)
        self.bottom, self.status, self.progress, self.btn = C.bottom_bar(tr("normalize"), self.start)
        self.append(Gtk.Separator())
        self.append(self.bottom)

        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", self._on_drop)
        self.add_controller(drop)
        self._update()
        GLib.timeout_add(100, self._ab_tick)

    # ================================================================ UI
    def _main(self):
        # dwie kolumny: lewa – utwory, wykres, odsłuch A/B; prawa – ustawienia i zapis.
        # Przy wąskim oknie (breakpoint w window.py) kolumny układają się jedna pod drugą.
        self.columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=40, homogeneous=True)
        self.columns.set_vexpand(False)       # rozciąganie wykresu kończy się na wysokości kolumn, nie okna
        for m in ("top", "bottom", "start", "end"):
            getattr(self.columns, f"set_margin_{m}")(28 if m in ("start", "end") else 24 if m == "top" else 0)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)      # wykres rozciąga się do dołu prawej kolumny
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28, valign=Gtk.Align.START)
        self.columns.append(left)
        self.columns.append(right)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        outer.append(self.columns)
        self.ab_holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)     # odsłuch A/B na całą szerokość
        for m in ("bottom", "start", "end"):
            getattr(self.ab_holder, f"set_margin_{m}")(28 if m != "bottom" else 24)
        outer.append(self.ab_holder)
        clamp = Adw.Clamp(maximum_size=1320, tightening_threshold=1000, child=outer)
        page = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=clamp)
        tg = Adw.PreferencesGroup(title=tr("a_tracks"), description=tr("a_tracks_sub"))
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
        left.append(tg)

        self.chart_group = Adw.PreferencesGroup(title=tr("chart_title"), description=tr("chart_sub"), visible=False)
        self.chart = AlbumChart()
        self.chart.set_vexpand(True)
        card = Gtk.Box(vexpand=True)
        self.chart_card = card
        card.add_css_class("card")
        card.add_css_class("chart-card")
        for m in ("top", "bottom", "start", "end"):
            getattr(self.chart, f"set_margin_{m}")(12)
        card.append(self.chart)
        self.chart_group.add(card)
        left.append(self.chart_group)

        mg = Adw.PreferencesGroup(title=tr("a_master"), description=tr("a_master_sub"))
        self.master_row = Adw.ComboRow(title=tr("master_style"),
                                       model=Gtk.StringList.new([tr("mp_" + k) for k in M.ORDER]))
        # niewidoczny „bliźniak” przycisków z nagłówka „Utwory” – nagłówki i karty obu kolumn zaczynają się równo
        ghost = Gtk.Button(icon_name="list-add-symbolic", valign=Gtk.Align.CENTER, opacity=0, can_focus=False,
                           can_target=False)
        ghost.add_css_class("flat")
        mg.set_header_suffix(ghost)
        self.master_row.connect("notify::selected", lambda *_: self._refresh_rows())
        mg.add(self.master_row)
        self.pv_track_row = Adw.ComboRow(title=tr("pv_track"), subtitle=tr("pv_sub"))
        mg.add(self.pv_track_row)
        pv = Adw.ActionRow(title=tr("pv_play"))
        self.pv_btn = Gtk.Button(icon_name="media-playback-start-symbolic", valign=Gtk.Align.CENTER,
                                 tooltip_text=tr("pv_play"))
        self.pv_btn.add_css_class("circular")
        self.pv_btn.add_css_class("suggested-action")
        self.pv_btn.connect("clicked", lambda *_: self.preview())
        self.pv_spin = Gtk.Spinner(valign=Gtk.Align.CENTER, visible=False)
        pv.add_suffix(self.pv_spin)
        pv.add_suffix(self.pv_btn)
        pv.set_activatable_widget(self.pv_btn)
        self.pv_row = pv
        mg.add(pv)
        right.append(mg)

        ng = Adw.PreferencesGroup(title=tr("a_norm"), description=tr("a_norm_sub"))
        # krótkie nazwy na liście (bez ucinania „…”), pełny opis w podpisie wiersza
        self.target_row = Adw.ComboRow(title=tr("target"),
                                       model=Gtk.StringList.new([tr("tshort_" + k) for k in N.TARGET_ORDER]))
        self.target_row.set_selected(N.TARGET_ORDER.index("cd"))
        self.manual_row = Adw.SpinRow.new_with_range(N.MANUAL_RANGE[0], N.MANUAL_RANGE[1], 0.5)
        self.manual_row.set_title(tr("manual_lufs"))
        self.manual_row.set_subtitle(tr("manual_hint"))
        self.manual_row.set_digits(1)
        self.manual_row.set_value(float(i18n.load_settings().get("manual_lufs", N.MANUAL_DEFAULT)))
        self.manual_row.add_css_class("manual-row")
        self.manual_row.connect("notify::value", lambda *_: self._on_manual_lufs())
        self.mode_row = Adw.ComboRow(title=tr("mode"), model=Gtk.StringList.new([tr("mshort_" + m) for m in N.MODES]))
        for r in (self.target_row, self.mode_row):
            r.connect("notify::selected", lambda *_: self._refresh_rows())
        ng.add(self.target_row)
        ng.add(self.manual_row)
        ng.add(self.mode_row)
        right.append(ng)

        o = Adw.PreferencesGroup(title=tr("output"))
        self.wavq_row = Adw.ComboRow(title=tr("wav_quality"),
                                     model=Gtk.StringList.new([tr("wshort_cd"), tr("wshort_hires")]))
        self.wavq_row.connect("notify::selected", lambda *_: self.wavq_row.set_subtitle(
            tr("wdesc_cd" if self.wavq_row.get_selected() == 0 else "wdesc_hires")))
        self.wavq_row.set_subtitle(tr("wdesc_cd"))
        o.add(self.wavq_row)
        fr = Adw.ActionRow(title=tr("formats"))
        self.fmt = {}
        for k, label in (("wav", "WAV"), ("mp3", "MP3"), ("mp4", "MP4")):
            c = Gtk.CheckButton(label=label, active=(k == "wav"), valign=Gtk.Align.CENTER)
            self.fmt[k] = c
            fr.add_suffix(c)
        o.add(fr)
        self.artist_row = Adw.EntryRow(title=tr("artist"))
        self.album_row = Adw.EntryRow(title=tr("album"))
        o.add(self.artist_row)
        o.add(self.album_row)
        self.cover_row = Adw.ActionRow(title=tr("cover"), subtitle=tr("cover_none"), activatable=True)
        self.cover_img = Gtk.Picture(content_fit=Gtk.ContentFit.COVER, visible=False)
        self.cover_img.set_size_request(44, 44)
        self.cover_img.add_css_class("cover-thumb")
        self.cover_rm = Gtk.Button(icon_name="edit-delete-symbolic", tooltip_text=tr("cover_remove"),
                                   valign=Gtk.Align.CENTER, visible=False)
        self.cover_rm.add_css_class("flat")
        self.cover_rm.connect("clicked", lambda *_: self.set_cover(None))
        self.cover_row.add_suffix(self.cover_img)
        self.cover_row.add_suffix(self.cover_rm)
        self.cover_row.connect("activated", lambda *_: self.choose_cover())
        o.add(self.cover_row)
        right.append(o)
        self.ab_holder.append(self._ab_group())
        return page

    def _ab_group(self):
        g = Adw.PreferencesGroup(title=tr("ab_title"), description=tr("ab_sub"), visible=False)
        self.ab_group = g
        self.ab_track_row = Adw.ComboRow(title=tr("ab_track"))
        self.ab_track_row.connect("notify::selected", lambda *_: self._ab_load())
        g.add(self.ab_track_row)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("card")
        for m in ("top", "bottom", "start", "end"):
            getattr(card, f"set_margin_{m}")(0)
        row = Gtk.Box(spacing=12)
        for m in ("top", "start", "end"):
            getattr(row, f"set_margin_{m}")(12)
        self.ab_play = Gtk.Button(icon_name="media-playback-start-symbolic", tooltip_text=tr("play"),
                                  valign=Gtk.Align.CENTER)
        self.ab_play.add_css_class("circular")
        self.ab_play.add_css_class("suggested-action")
        self.ab_play.connect("clicked", lambda *_: self.ab.toggle())
        sw = Gtk.Box(valign=Gtk.Align.CENTER)
        sw.add_css_class("linked")
        self.ab_a = Gtk.ToggleButton(label=tr("ab_a"))
        self.ab_b = Gtk.ToggleButton(label=tr("ab_b"), active=True, group=self.ab_a)
        for b, side in ((self.ab_a, "a"), (self.ab_b, "b")):
            b.add_css_class("ab-side")
            b.connect("toggled", lambda btn, side=side: btn.get_active() and self.ab.set_side(side))
            sw.append(b)
        self.ab_pos = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        self.ab_pos.set_hexpand(True)
        self.ab_pos.set_draw_value(False)
        self._ab_pos_h = self.ab_pos.connect("change-value", lambda _s, _c, v: (self.ab.seek(v), False)[1])
        self.ab_time = Gtk.Label(label="0:00 / 0:00")
        self.ab_time.add_css_class("numeric")
        for w in (self.ab_play, sw, self.ab_pos, self.ab_time):
            row.append(w)
        card.append(row)
        meters = Gtk.Box(spacing=24, homogeneous=True)
        for m in ("start", "end"):
            getattr(meters, f"set_margin_{m}")(12)
        self.ab_meter_boxes = {}
        for side in ("a", "b"):
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            col.append(self.ab_meters[side])
            lab = Gtk.Label(label=tr("ab_" + side))
            lab.add_css_class("caption-heading")
            col.append(lab)
            self.ab_meter_boxes[side] = col
            meters.append(col)
        card.append(meters)
        # dokładna głośność na żywo (EBU R128) – obie wersje, tak jak je słychać po wyrównaniu
        grid = Gtk.Grid(column_spacing=24, row_spacing=4, halign=Gtk.Align.CENTER)
        for m in ("top", "bottom"):
            getattr(grid, f"set_margin_{m}")(6)
        self.ab_vals = {}
        for c, side in enumerate(("a", "b"), 1):
            h = Gtk.Label(label=tr("ab_" + side), xalign=1)
            h.add_css_class("caption-heading")
            grid.attach(h, c, 0, 1, 1)
            self.ab_vals[side + "_h"] = h
        for r, key in enumerate(("m", "s", "i"), 1):
            lab = Gtk.Label(label=tr("ab_" + key), xalign=0)
            lab.add_css_class("caption")
            lab.add_css_class("dim-label")
            grid.attach(lab, 0, r, 1, 1)
            for c, side in enumerate(("a", "b"), 1):
                v = Gtk.Label(label="—", xalign=1, width_chars=11)
                v.add_css_class("numeric")
                v.add_css_class("lufs-value")
                if key == "s":
                    v.add_css_class("lufs-big")
                grid.attach(v, c, r, 1, 1)
                self.ab_vals[side + key] = v
        card.append(grid)
        self.ab_info = Gtk.Label(xalign=0, wrap=True)
        self.ab_info.add_css_class("caption")
        self.ab_info.add_css_class("dim-label")
        for m in ("bottom", "start", "end"):
            getattr(self.ab_info, f"set_margin_{m}")(12)
        card.append(self.ab_info)
        self.ab_card = card
        g.add(card)
        self.ab_stale_lbl = Gtk.Label(label=tr("ab_stale"), wrap=True, xalign=0, visible=False)
        self.ab_stale_lbl.add_css_class("ab-stale")
        g.add(self.ab_stale_lbl)
        return g

    # ================================================================ pliki
    def _on_drop(self, _t, value, *_):
        audio, png = C.collect_audio(value.get_files())
        if audio:
            self.add_files(audio)
        if png:
            self.set_cover(png)
        return True

    def choose_files(self):
        C.open_audio_dialog(self.win, self.add_files)

    def add_files(self, paths):
        if self.busy:
            return
        known = {t.path for t in self.tracks}
        new = [ATrack(p) for p in paths if p not in known]
        for t in new:
            L.log(f"dodano utwór {os.path.basename(t.path)}", tag="ui")
        if not new:
            return
        self.tracks = sorted(self.tracks + new, key=lambda t: os.path.basename(t.path).lower())
        self._rebuild()
        for t in new:
            fut = self.ex.submit(N.analyze, t.path)
            fut.add_done_callback(lambda f, t=t: GLib.idle_add(self._analyzed, t, f))
        self._update()

    def remove(self, t):
        if not self.busy:
            self.tracks.remove(t)
            self._rebuild()
            self._update()

    def clear(self):
        if not self.busy:
            self.tracks = []
            self.results = None
            self.ab.stop()
            self.ab_group.set_visible(False)
            self._rebuild()
            self._update()

    def _rebuild(self):
        self.list.remove_all()
        for n, t in enumerate(self.tracks, 1):
            row = Adw.ActionRow(title=C.esc(os.path.basename(t.path)))
            num = Gtk.Label(label=f"{n:02d}", width_chars=3)
            num.add_css_class("dim-label")
            num.add_css_class("numeric")
            row.add_prefix(num)
            t.spin = Gtk.Spinner(spinning=t.info is None, visible=t.info is None, valign=Gtk.Align.CENTER)
            t.ok_icon = Gtk.Image(icon_name="emblem-ok-symbolic", visible=False)
            t.ok_icon.add_css_class("badge-ok")
            rm = Gtk.Button(icon_name="user-trash-symbolic", tooltip_text=tr("remove"), valign=Gtk.Align.CENTER)
            rm.add_css_class("flat")
            rm.connect("clicked", lambda *_, t=t: self.remove(t))
            for w in (t.spin, t.ok_icon, rm):
                row.add_suffix(w)
            t.row = row
            self.list.append(row)
        self._refresh_rows()

    def _analyzed(self, t, fut):
        try:
            t.info = fut.result()
        except Exception as e:  # noqa: BLE001
            t.info = N.NormInfo(t.path, error=str(e))
        if t.spin:
            t.spin.set_spinning(False)
            t.spin.set_visible(False)
        self._refresh_rows()
        self._update()
        return False

    def _target(self):
        return N.TARGET_ORDER[self.target_row.get_selected()]

    def _manual(self):
        return self.manual_row.get_value()

    def _on_manual_lufs(self):
        s = i18n.load_settings()
        s["manual_lufs"] = self._manual()
        i18n.save_settings(s)
        self._refresh_rows()

    def _mode(self):
        return N.MODES[self.mode_row.get_selected()]

    def _master(self):
        return M.ORDER[self.master_row.get_selected()]

    def _key(self):
        return (self._target(), self._manual() if self._target() == "manual" else None, self._mode(), self._master(),
                tuple(t.path for t in self.tracks))

    def _refresh_rows(self):
        infos = [t.info for t in self.tracks if t.info and not t.info.error]
        pl = N.plan(infos, self._target(), self._mode(), self._manual()) if infos and all(t.info for t in self.tracks) else {}
        for t in self.tracks:
            if not t.row:
                continue
            if t.info is None:
                t.row.set_subtitle(tr("analyzing"))
            elif t.info.error:
                t.row.set_subtitle(f"⚠ {tr('analysis_failed')}: {C.esc(t.info.error[:70])}")
            else:
                i = t.info
                s = tr("track_meta", dur=C.fmt_dur(i.duration), lufs=i.lufs, tp=i.true_peak)
                if t.path in pl:
                    kind, val = pl[t.path]
                    db = val if kind == "gain" else val - (i.loud if kind == "loud" else i.lufs)
                    s += tr("change", db=db)
                t.row.set_subtitle(s)
        ceil = N.ceiling(self._target(), self._manual())
        self.target_row.set_subtitle(tr("tdesc_" + self._target()) + " · " +
                                     tr("ceiling_info_loud" if ceil < N.CEILING_DBTP else "ceiling_info", ceil=ceil))
        self.manual_row.set_visible(self._target() == "manual")
        self._ab_check_stale()
        self.mode_row.set_subtitle(tr("mdesc_" + self._mode()))
        self.master_row.set_subtitle(tr(f"mp_{self._master()}_d"))
        self._refresh_chart(pl)

    def _refresh_chart(self, pl):
        """Po normalizacji (te same ustawienia) – zmierzone wartości; wcześniej – przewidywane."""
        target = N.target_value(self._target(), self._manual())
        if self.results and self.results_key == self._key():
            items = [dict(n=n, before=r["info"].lufs, after=r["stats"]["lufs"], lra_before=r["info"].lra,
                          lra_after=r["stats"]["lra"]) for n, r in enumerate(self.results, 1)]
            self.chart.set_data(items, target, True)
        elif pl:
            items = []
            for n, t in enumerate(self.tracks, 1):
                if t.path in pl:
                    i = t.info
                    items.append(dict(n=n, before=i.lufs, after=N.predicted_lufs(i, *pl[t.path]),
                                      lra_before=i.lra, lra_after=i.lra))
            self.chart.set_data(items, target, False)
        else:
            self.chart.set_data([], target, False)
        self.chart_group.set_visible(bool(self.chart.items))

    # ================================================================ okładka
    def choose_cover(self):
        dlg = Gtk.FileDialog(title=tr("cover"))
        flt = Gtk.FileFilter(name=tr("images_filter"))
        flt.add_suffix("png")
        store = Gio.ListStore.new(Gtk.FileFilter)
        store.append(flt)
        dlg.set_filters(store)

        def done(d, res):
            try:
                self.set_cover(d.open_finish(res).get_path())
            except GLib.Error:
                pass
        dlg.open(self.win, None, done)

    def set_cover(self, path):
        self.cover = path
        if path:
            self.cover_img.set_filename(path)
            self.cover_row.set_subtitle(C.esc(os.path.basename(path)))
        else:
            self.cover_row.set_subtitle(tr("cover_none"))
        self.cover_img.set_visible(bool(path))
        self.cover_rm.set_visible(bool(path))

    # ================================================================ normalizacja
    def _infos(self):
        return [t.info for t in self.tracks if t.info and not t.info.error]

    def _update(self):
        self.stack.set_visible_child_name("main" if self.tracks else "empty")
        self.bottom.set_visible(bool(self.tracks))
        analyzing = any(t.info is None for t in self.tracks)
        self.btn.set_sensitive(bool(self._infos()) and not analyzing and not self.busy)
        if not self.busy:
            if analyzing:
                self.status.set_text(tr("analyzing"))
            else:
                infos = self._infos()
                tot = sum(i.duration for i in infos)
                self.status.set_text(tr("count_dur", count=count(len(infos), "song"), dur=C.fmt_dur(tot))
                                     if infos else "")
        self._pv_refresh()
        self.pv_btn.set_sensitive(self.pv_btn.get_sensitive() and not analyzing)

    def start(self):
        formats = [k for k, c in self.fmt.items() if c.get_active()]
        if not formats:
            self.win.toast(tr("no_format"))
            return
        infos = self._infos()
        if not infos:
            return
        out_dir = os.path.join(os.path.dirname(infos[0].path), "normalized")
        meta = dict(artist=self.artist_row.get_text().strip(), album=self.album_row.get_text().strip())
        wavq = "cd" if self.wavq_row.get_selected() == 0 else "hires"
        target, mode, cover, mkey, manual = self._target(), self._mode(), self.cover, self._master(), self._manual()
        run_key = self._key()
        self.ab.stop()
        self.busy = True
        for t in self.tracks:
            t.ok_icon.set_visible(False)
        self.progress.set_fraction(0)
        self.progress.set_visible(True)
        self.status.set_text(tr("normalizing", done=0, total=len(infos)))
        self._update()

        def prog(idx, done, total):
            GLib.idle_add(self._progress, infos[idx].path, done, total)

        def work():
            try:
                res = jobs.normalize_album(self.ex, infos, target, mode, out_dir, formats, wavq, cover, meta, prog,
                                           master_key=mkey, manual=manual)
                text = jobs.report_text(res, tr, target, mode, mkey, manual)
                self.results_key = run_key
                with open(os.path.join(out_dir, "raport.txt" if i18n.LANG == "pl" else "report.txt"), "w") as f:
                    f.write(text + "\n")
                GLib.idle_add(self._done, out_dir, res, text, None)
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                GLib.idle_add(self._done, out_dir, None, None, str(e))
        threading.Thread(target=work, daemon=True).start()

    def _progress(self, path, done, total):
        self.progress.set_fraction(done / total)
        self.status.set_text(tr("normalizing", done=done, total=total))
        for t in self.tracks:
            if t.path == path:
                t.ok_icon.set_visible(True)
        return False

    def _done(self, out_dir, res, text, err):
        self.busy = False
        self.progress.set_visible(False)
        self._update()
        if err:
            d = Adw.AlertDialog(heading=tr("error"), body=err)
            d.add_response("close", tr("close"))
            d.present(self.win)
            return False
        self.results = res
        self._refresh_rows()
        self._ab_fill()
        self.win.app.notify(tr("done_title"), tr("notif_done", count=count(len(res), "song")))
        body = tr("done_body", count=count(len(res), "song"))
        sq = jobs.squashed(res)
        if sq:
            body += tr("warn_squash", tracks=", ".join(f"{n:02d}" for n in sq))
        d = Adw.AlertDialog(heading=tr("done_title"), body=body)
        d.add_response("report", tr("show_report"))
        d.add_response("close", tr("close"))
        d.add_response("open", tr("open_folder"))
        d.set_response_appearance("open", Adw.ResponseAppearance.SUGGESTED)
        d.set_default_response("open")

        def resp(_d, r):
            if r == "open":
                C.open_folder(self.win, out_dir)
            elif r == "report":
                self.show_report(text)
        d.connect("response", resp)
        d.present(self.win)
        return False

    # ================================================================ A/B
    def _ab_fill(self):
        res = [r for r in (self.results or []) if r["files"]]
        self.ab_group.set_visible(bool(res))
        self.ab_group.set_description(tr("ab_sub"))
        self.ab_track_row.set_visible(True)
        self._ab_key = self.results_key
        self._ab_res = res
        names = [f"{n:02d} · {os.path.basename(r['info'].path)}" for n, r in enumerate(self.results or [], 1)
                 if r["files"]]
        self.ab_track_row.set_model(Gtk.StringList.new(names))
        if res:
            self.ab_track_row.set_selected(0)
            self._ab_load()

    def _ab_load(self):
        res = getattr(self, "_ab_res", None)
        i = self.ab_track_row.get_selected()
        if not res or i >= len(res):
            return
        r = res[i]
        f = r["files"]
        b = (f.get("wav") or f.get("mp4") or f.get("mp3"))["path"]
        self._ab_open(r["info"].path, b, r["info"].lufs, r["stats"]["lufs"])

    def _ab_open(self, a, b, a_lufs, b_lufs):
        """Ładuje parę A/B (cały utwór po normalizacji albo 20-sekundową próbkę) z wyrównaną głośnością."""
        ga, gb, ref = ABPlayer.matched_gains(a_lufs, b_lufs)
        try:
            self.ab.load(a, b, ga, gb)
        except Exception as e:  # noqa: BLE001
            L.log(f"A/B: {e}", "error", tag="ab")
            self.win.toast(str(e))
            return
        self._ab_set_stale(False)
        for m in self.ab_meters.values():
            m.reset()
        self.ab_info.set_text(tr("ab_files", a=a_lufs, b=b_lufs, d=abs(a_lufs - b_lufs)))
        self._ab_cur = None
        for v in self.ab_vals.values():
            if v.get_label() != tr("ab_a") and v.get_label() != tr("ab_b"):
                v.set_label("…")
        paths = (a, b)
        self._ab_gains = (ga, gb)
        todo = [p for p in paths if p not in self._curves]
        if not todo:
            self._ab_set_curves(paths)
            return
        self.ab_info.set_text(tr("ab_calc"))
        for pth in todo:
            fut = self.ex.submit(jobs.loudness_curves, pth)
            fut.add_done_callback(lambda f, pth=pth: GLib.idle_add(self._ab_curve_done, pth, paths, f,
                                                                    a_lufs, b_lufs))

    def _ab_curve_done(self, pth, paths, fut, a_lufs, b_lufs):
        try:
            self._curves[pth] = fut.result()
        except Exception as e:  # noqa: BLE001
            L.log(f"A/B: pomiar głośności {os.path.basename(pth)}: {e}", "error", tag="ab")
            return False
        if all(p in self._curves for p in paths) and self.ab.paths == paths:
            self.ab_info.set_text(tr("ab_files", a=a_lufs, b=b_lufs, d=abs(a_lufs - b_lufs)))
            self._ab_set_curves(paths)
        return False

    def _ab_set_curves(self, paths):
        self._ab_cur = (self._curves[paths[0]], self._curves[paths[1]], *self._ab_gains)
        ca, cb, ga, gb = self._ab_cur
        self.ab_vals["ai"].set_label(self._fmt_lufs(ca["integrated"] + ga))
        self.ab_vals["bi"].set_label(self._fmt_lufs(cb["integrated"] + gb))
        self._ab_tick()

    @staticmethod
    def _fmt_lufs(v):
        return "−∞" if v < -69 else f"{num(v)} LUFS"

    @staticmethod
    def _at(curve, pos, window):
        arr = curve
        i = int(round((pos - window) / 0.1))
        i = max(0, min(len(arr) - 1, i))
        return float(arr[i]) if len(arr) else -70.0

    def _ab_peak(self, db):
        if self._ab_cur is None:            # dopóki krzywe się liczą, miernik słyszanej wersji pokazuje szczyty
            self.ab_meters[self.ab.side].set_level(db)

    def _ab_sync(self):
        p = self.ab.playing
        self.ab_play.set_icon_name("media-playback-pause-symbolic" if p else "media-playback-start-symbolic")
        self.ab_play.set_tooltip_text(tr("pause") if p else tr("play"))

    def _ab_tick(self):
        if self.ab.pipe:
            self.ab.check_stall()
            pend = self.ab.pending_position()
            d, p = self.ab.duration(), (pend if pend is not None else self.ab.position())
            self.ab_pos.handler_block(self._ab_pos_h)
            self.ab_pos.set_range(0, max(d, 0.1))
            self.ab_pos.set_value(p)
            self.ab_pos.handler_unblock(self._ab_pos_h)
            self.ab_time.set_text(f"{C.fmt_dur(p)} / {C.fmt_dur(d)}")
            if self._ab_cur is not None:
                ca, cb, ga, gb = self._ab_cur
                vals = {}
                for side, c, g in (("a", ca, ga), ("b", cb, gb)):
                    vals[side] = (self._at(c["momentary"], p, 0.4) + g, self._at(c["short"], p, 3.0) + g)
                    self.ab_vals[side + "m"].set_label(self._fmt_lufs(vals[side][0]))
                    self.ab_vals[side + "s"].set_label(self._fmt_lufs(vals[side][1]))
                heard = self.ab.side
                for side in ("a", "b"):
                    for key in ("_h", "m", "s", "i"):
                        w = self.ab_vals[side + key]
                        (w.add_css_class if side == heard else w.remove_css_class)("ab-heard")
                for side in ("a", "b"):
                    if self.ab.playing:                           # każdy miernik = głośność chwilowa swojej wersji
                        self.ab_meters[side].set_level(vals[side][0])
                    (self.ab_meter_boxes[side].remove_css_class if side == heard
                     else self.ab_meter_boxes[side].add_css_class)("ab-quiet")
        return True

    # ================================================================ próbka i aktualność odsłuchu
    def _ab_set_stale(self, stale):
        self._ab_stale = stale
        self.ab_card.set_visible(not stale)
        self.ab_track_row.set_visible(not stale and self._ab_key == self.results_key)
        self.ab_stale_lbl.set_visible(stale)

    def _ab_check_stale(self):
        """Zmiana masteringu, poziomu, sposobu albo listy utworów -> stary odsłuch nie pasuje: stop i podpowiedź.
        Powrót do ustawień ostatniej normalizacji -> jej odsłuch wraca."""
        if not hasattr(self, "ab_card") or not self.ab_group.get_visible():
            return
        cur = self._key()
        if not self._ab_stale and self._ab_key is not None and self._ab_key != cur:
            self.ab.stop()
            self._ab_sync()
            self._ab_set_stale(True)
        elif self._ab_stale and self.results and self.results_key == cur:
            self._ab_fill()

    def _pv_tracks(self):
        return [t for t in self.tracks if t.info and not t.info.error]

    def _pv_refresh(self):
        names = [f"{n:02d} · {os.path.basename(t.path)}" for n, t in enumerate(self._pv_tracks(), 1)]
        sel = self.pv_track_row.get_selected()
        self.pv_track_row.set_model(Gtk.StringList.new(names))
        if names:
            self.pv_track_row.set_selected(min(sel, len(names) - 1) if sel != Gtk.INVALID_LIST_POSITION else 0)
        self.pv_btn.set_sensitive(bool(names) and not self.busy)

    def preview(self):
        tracks = self._pv_tracks()
        i = self.pv_track_row.get_selected()
        if not tracks or i >= len(tracks) or self.busy:
            return
        t = tracks[i]
        infos = self._infos()
        pl = N.plan(infos, self._target(), self._mode(), self._manual())
        kind, val = pl[t.path]
        gain = val if kind == "gain" else val - (t.info.loud if kind == "loud" else t.info.lufs)
        ceil = N.ceiling(self._target(), self._manual())
        mkey, key = self._master(), self._key()
        self.ab.stop()
        self.pv_btn.set_sensitive(False)
        self.pv_spin.set_visible(True)
        self.pv_spin.set_spinning(True)
        self.pv_row.set_subtitle(tr("pv_busy"))
        fut = self.ex.submit(jobs.preview_excerpt, t.path, mkey, gain, ceil)
        fut.add_done_callback(lambda f: GLib.idle_add(self._preview_done, t, mkey, key, f))

    def _preview_done(self, t, mkey, key, fut):
        self.pv_spin.set_spinning(False)
        self.pv_spin.set_visible(False)
        self.pv_btn.set_sensitive(True)
        self.pv_row.set_subtitle("")
        try:
            r = fut.result()
        except Exception as e:  # noqa: BLE001
            L.log(f"próbka: {e}", "error", tag="preview")
            self.win.toast(str(e))
            return False
        target = self.target_row.get_model().get_string(self.target_row.get_selected())
        self.ab_group.set_visible(True)
        self.ab_group.set_description(tr("pv_desc", name=os.path.basename(t.path), preset=tr("mp_" + mkey),
                                         target=target))
        self._ab_key = key
        self._ab_open(r["a"], r["b"], r["a_lufs"], r["b_lufs"])
        self.ab_track_row.set_visible(False)
        self.ab.play()
        return False

    def show_report(self, text):
        w = Adw.Window(transient_for=self.win, modal=True, title=tr("show_report"), default_width=860,
                       default_height=520)
        tv = Adw.ToolbarView()
        tv.add_top_bar(Adw.HeaderBar())
        view = Gtk.TextView(editable=False, monospace=True, left_margin=16, top_margin=12, right_margin=16)
        view.get_buffer().set_text(text)
        tv.set_content(Gtk.ScrolledWindow(child=view))
        w.set_content(tv)
        w.present()
