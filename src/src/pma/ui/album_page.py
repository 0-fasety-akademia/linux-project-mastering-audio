"""Zakładka ALBUM: normalizacja głośności gotowych utworów (bez zmiany brzmienia)."""
import os
import threading
import traceback

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import i18n  # noqa: E402
from ..engine import jobs  # noqa: E402
from ..engine import normalize as N  # noqa: E402
from ..i18n import count, tr  # noqa: E402
from . import common as C  # noqa: E402
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

    # ================================================================ UI
    def _main(self):
        page = Adw.PreferencesPage()
        tg = Adw.PreferencesGroup(title=tr("a_tracks"))
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

        ng = Adw.PreferencesGroup(title=tr("a_norm"), description=tr("a_norm_sub"))
        self.target_row = Adw.ComboRow(title=tr("target"),
                                       model=Gtk.StringList.new([tr("target_" + k) for k in N.TARGET_ORDER]))
        self.target_row.set_selected(N.TARGET_ORDER.index("cd"))
        self.mode_row = Adw.ComboRow(title=tr("mode"), model=Gtk.StringList.new([tr("mode_" + m) for m in N.MODES]))
        for r in (self.target_row, self.mode_row):
            r.connect("notify::selected", lambda *_: self._refresh_rows())
            ng.add(r)
        page.add(ng)

        o = Adw.PreferencesGroup(title=tr("output"))
        self.wavq_row = Adw.ComboRow(title=tr("wav_quality"), model=Gtk.StringList.new([tr("wav_cd"), tr("wav_hires")]))
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
        page.add(o)
        return page

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

    def _mode(self):
        return N.MODES[self.mode_row.get_selected()]

    def _refresh_rows(self):
        infos = [t.info for t in self.tracks if t.info and not t.info.error]
        pl = N.plan(infos, self._target(), self._mode()) if infos and all(t.info for t in self.tracks) else {}
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
        target, mode, cover = self._target(), self._mode(), self.cover
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
                res = jobs.normalize_album(self.ex, infos, target, mode, out_dir, formats, wavq, cover, meta, prog)
                text = jobs.report_text(res, tr, target, mode)
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
        self.win.app.notify(tr("done_title"), tr("notif_done", count=count(len(res), "song")))
        d = Adw.AlertDialog(heading=tr("done_title"), body=tr("done_body", count=count(len(res), "song")))
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
