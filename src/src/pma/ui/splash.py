"""Ekran startowy w stylu GIMP-a: duża grafika bez ramki, wersja i pasek ładowania."""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from .. import APP_NAME, VERSION, paths  # noqa: E402
from ..i18n import tr  # noqa: E402

RATIO = 400 / 640


class Splash(Gtk.Window):
    def __init__(self, app):
        super().__init__(application=app, decorated=False, resizable=False)
        self.add_css_class("splash")
        self.set_title(APP_NAME)
        w = 640
        try:
            mon = Gdk.Display.get_default().get_monitors().get_item(0)
            geo = mon.get_geometry()
            w = int(max(640, min(900, geo.width * 0.42)))
        except Exception:  # noqa: BLE001
            pass
        h = int(w * RATIO)
        self.set_default_size(w, h)
        s = w / 640.0

        frame = Gtk.Overlay()
        frame.add_css_class("splash-frame")
        frame.set_overflow(Gtk.Overflow.HIDDEN)
        pic = Gtk.Picture.new_for_filename(paths.data("splash.png"))
        pic.set_content_fit(Gtk.ContentFit.FILL)
        pic.set_size_request(w, h)
        frame.set_child(pic)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(6 * s), valign=Gtk.Align.END)
        box.set_margin_start(int(40 * s))
        box.set_margin_end(int(40 * s))
        box.set_margin_bottom(int(34 * s))
        row = Gtk.Box(spacing=12)
        self.status = Gtk.Label(label=tr("loading_engine"), xalign=0, hexpand=True)
        self.status.add_css_class("splash-status")
        ver = Gtk.Label(label=f"v{VERSION}", xalign=1)
        ver.add_css_class("splash-status")
        row.append(self.status)
        row.append(ver)
        self.bar = Gtk.ProgressBar()
        self.bar.add_css_class("splash-progress")
        box.append(row)
        box.append(self.bar)
        frame.add_overlay(box)

        credits = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(2 * s),
                          halign=Gtk.Align.END, valign=Gtk.Align.END)
        credits.set_margin_end(int(40 * s))
        credits.set_margin_bottom(int(78 * s))
        made = Gtk.Label(label=tr("made_by"), xalign=1)
        made.add_css_class("splash-made")
        sup = Gtk.Label(label=tr("supported_by"), xalign=1)
        sup.add_css_class("splash-supported")
        credits.append(made)
        credits.append(sup)
        frame.add_overlay(credits)
        self.set_child(frame)

    def update(self, fraction, text=None):
        self.bar.set_fraction(fraction)
        if text:
            self.status.set_text(text)
        return False
