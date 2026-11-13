"""Punkt wejścia aplikacji: splash -> ładowanie silnika -> okno główne."""
import os
import sys
import threading
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import APP_ID, APP_NAME, VERSION, i18n, paths  # noqa: E402
from .i18n import tr  # noqa: E402

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_SPLASH = 1.6


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.win = None
        self.splash = None
        self.ex = None
        self.pending_files = []
        GLib.set_application_name(APP_NAME)

    # ------------------------------------------------------------------
    def do_startup(self):
        Adw.Application.do_startup(self)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.DEFAULT)
        css = Gtk.CssProvider()
        css.load_from_path(os.path.join(os.path.dirname(__file__), "ui", "style.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        theme.add_search_path(paths.data("icons", "hicolor"))

        lang = Gio.SimpleAction.new_stateful("language", GLib.VariantType.new("s"), GLib.Variant("s", i18n.LANG))
        lang.connect("activate", self._on_language)
        self.add_action(lang)
        from .ui import themes
        tkey = i18n.load_settings().get("theme", "system")
        themes.apply(tkey)
        theme = Gio.SimpleAction.new_stateful("theme", GLib.VariantType.new("s"), GLib.Variant("s", themes.CURRENT))
        theme.connect("activate", self._on_theme)
        self.add_action(theme)
        for name, cb in (("about", self._on_about), ("quit", lambda *_: self.really_quit())):
            a = Gio.SimpleAction.new(name, None)
            a.connect("activate", cb)
            self.add_action(a)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self._sync_icon()

    def do_activate(self):
        if self.win:
            self.win.present()
            return
        if self.splash:
            return
        from .ui.splash import Splash
        self.splash = Splash(self)
        self.splash.present()
        threading.Thread(target=self._load, daemon=True).start()

    def do_open(self, files, _n, _hint):
        self.pending_files += [f.get_path() for f in files if f.get_path()]
        if self.win:
            self.win.add_files(self.pending_files)
            self.pending_files = []
            self.win.present()
        else:
            self.do_activate()

    # ------------------------------------------------------------------
    def _load(self):
        t0 = time.time()
        step = lambda f, txt=None: GLib.idle_add(self.splash.update, f, txt)  # noqa: E731
        step(0.1, tr("loading_engine"))
        from .engine import jobs, vocal  # noqa: F401  (numpy / scipy)
        step(0.4)
        from . import log as L
        ex = jobs.pool()
        L.start_reader(ex.log_queue)
        L.log(f"{APP_NAME} v{VERSION}", "ok", tag="start")
        L.log(f"Python {sys.version.split()[0]}, GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()}, "
              f"libadwaita {Adw.get_major_version()}.{Adw.get_minor_version()}", tag="start")
        L.log(f"pula procesów: {jobs.workers()} × spawn", tag="start")
        futs = [ex.submit(jobs.warm) for _ in range(jobs.workers())]
        for n, f in enumerate(futs, 1):
            f.result()
            step(0.4 + 0.4 * n / len(futs))
        self.ex = ex
        step(0.85, tr("loading_ui"))
        from .ui import window  # noqa: F401
        rest = MIN_SPLASH - (time.time() - t0)
        if rest > 0:
            time.sleep(rest)
        step(1.0, tr("ready"))
        time.sleep(0.25)
        GLib.idle_add(self._show_main)

    def _show_main(self):
        from .ui.window import MainWindow
        self.win = MainWindow(self, self.ex)
        self.win.connect("close-request", self._on_close)
        self.win.present()
        if self.splash:
            self.splash.destroy()
            self.splash = None
        if self.pending_files:
            self.win.add_files(self.pending_files)
            self.pending_files = []
        return False

    def _on_close(self, win):
        if win.busy:                      # mastering w toku – zapytaj
            d = Adw.AlertDialog(heading=tr("quit_busy_title"), body=tr("quit_busy_body"))
            d.add_response("cancel", tr("cancel"))
            d.add_response("quit", tr("quit"))
            d.set_response_appearance("quit", Adw.ResponseAppearance.DESTRUCTIVE)
            d.set_default_response("cancel")
            d.connect("response", lambda _d, r: r == "quit" and self.really_quit())
            d.present(win)
            return True
        self.really_quit()
        return True

    def really_quit(self):
        if self.win:
            self.win.shutdown()
        if self.ex:
            self.ex.shutdown(wait=False, cancel_futures=True)
        self.quit()

    def notify(self, title, body):
        note = Gio.Notification.new(title)
        note.set_body(body)
        note.set_icon(Gio.ThemedIcon.new(APP_ID))
        self.send_notification(None, note)

    # ------------------------------------------------------------------
    def _sync_icon(self):
        try:
            from . import iconsync
            iconsync.apply()
        except Exception as e:  # noqa: BLE001
            print("icon sync:", e)

    def _on_theme(self, action, value):
        from .ui import themes
        key = value.get_string()
        action.set_state(value)
        themes.apply(key)
        s = i18n.load_settings()
        s["theme"] = key
        i18n.save_settings(s)

    def _on_language(self, action, value):
        lang = value.get_string()
        action.set_state(value)
        s = i18n.load_settings()
        s["language"] = lang
        i18n.save_settings(s)
        if self.win and lang != i18n.LANG:
            self.win.toast(i18n.S[lang]["lang_restart"])

    def _on_about(self, *_):
        d = Adw.AboutDialog(application_name=APP_NAME, application_icon=APP_ID, version=VERSION,
                            developer_name=tr("made_by") + "\n" + tr("supported_by"),
                            comments=tr("about_comments"),
                            website="https://github.com/jgu-linux-apps/linux-project-mastering-audio")
        d.set_developers(["JGu"])
        d.add_credit_section(tr("supported_by").replace(" Claude", ""), ["Claude (Anthropic)"])
        d.present(self.win)


def main():
    app = App()
    return app.run(sys.argv)
