"""Okno główne: dwie zakładki – WOKAL (mastering i scalanie ścieżek) i ALBUM (normalizacja)."""
import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from .. import APP_NAME, i18n  # noqa: E402
from .terminal import MiniTerminal  # noqa: E402
from ..i18n import tr  # noqa: E402
from .album_page import AlbumPage  # noqa: E402
from .vocal_page import VocalPage  # noqa: E402


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app, executor):
        super().__init__(application=app, title=APP_NAME)
        self.app = app
        self.set_default_size(1280, 900)
        self.set_size_request(780, 620)

        self.vocal = VocalPage(self, executor)
        self.album = AlbumPage(self, executor)
        self.views = Adw.ViewStack()
        self.views.add_titled_with_icon(self.vocal, "vocal", tr("tab_vocal"), "audio-input-microphone-symbolic")
        self.views.add_titled_with_icon(self.album, "album", tr("tab_album"), "media-optical-symbolic")

        hb = Adw.HeaderBar()
        hb.set_title_widget(Adw.ViewSwitcher(stack=self.views, policy=Adw.ViewSwitcherPolicy.WIDE))
        menu = Gio.Menu()
        lang = Gio.Menu()
        lang.append("Polski", "app.language::pl")
        lang.append("English", "app.language::en")
        menu.append_submenu(tr("language"), lang)
        theme = Gio.Menu()
        for k in ("system", "neon", "holo", "analog", "pro"):
            theme.append(tr("theme_" + k), f"app.theme::{k}")
        menu.append_submenu(tr("theme"), theme)
        menu.append(tr("about"), "app.about")
        menu.append(tr("quit"), "app.quit")
        hb.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu, primary=True))
        self.term_btn = Gtk.ToggleButton(icon_name="utilities-terminal-symbolic", tooltip_text=tr("terminal"))
        hb.pack_end(self.term_btn)

        tv = Adw.ToolbarView()
        tv.add_top_bar(hb)
        overlay = Gtk.Overlay(child=self.views)
        self.term = MiniTerminal(on_close=lambda: self.term_btn.set_active(False))
        self.term.set_halign(Gtk.Align.END)
        self.term.set_valign(Gtk.Align.START)
        for m in ("top", "end"):
            getattr(self.term, f"set_margin_{m}")(12)
        overlay.add_overlay(self.term)
        self.term_btn.connect("toggled", self._on_term)
        self.term.set_visible(False)          # schowany przy starcie – otwiera się dopiero po kliknięciu
        self.toasts = Adw.ToastOverlay(child=overlay)
        tv.set_content(self.toasts)
        self.set_content(tv)
        # wąskie okno: zakładka Album w jednej kolumnie
        bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 960sp"))
        bp.add_setter(self.album.columns, "orientation", Gtk.Orientation.VERTICAL)
        bp.add_setter(self.album.columns, "homogeneous", False)
        self.add_breakpoint(bp)
        if os.environ.get("PMA_START_TAB") == "album":
            self.views.set_visible_child_name("album")

    def _on_term(self, btn):
        on = btn.get_active()
        self.term.set_visible(on)

    @property
    def busy(self):
        return self.vocal.busy or self.album.busy

    def toast(self, text):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))

    def add_files(self, paths):
        page = self.views.get_visible_child()
        page.add_files(paths)

    def shutdown(self):
        self.vocal.mixer.stop()
        self.album.ab.stop()
