"""Mini-terminal w prawym górnym rogu – na żywo pokazuje, co robi silnik."""
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk, Pango  # noqa: E402

from .. import log as L  # noqa: E402
from ..i18n import tr  # noqa: E402

COLORS = {"time": "#5c6890", "tag": "#00e5ff", "ok": "#3ddc84", "warn": "#ffcb6b", "error": "#ff5370",
          "info": "#c8d3f5", "sep": "#8b5cf6"}
MAX_LINES = 600


class MiniTerminal(Gtk.Box):
    def __init__(self, on_close):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("mini-term")
        self.set_size_request(470, 230)

        head = Gtk.Box(spacing=6)
        head.add_css_class("term-head")
        for c in ("#ff5f56", "#ffbd2e", "#27c93f"):
            dot = Gtk.Label(label="●")
            dot.set_markup(f'<span foreground="{c}">●</span>')
            head.append(dot)
        title = Gtk.Label(label="pma@linux: ~/mastering", hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        title.add_css_class("term-title")
        title.set_tooltip_text(tr("terminal"))
        head.append(title)
        clr = Gtk.Button(icon_name="edit-clear-symbolic", tooltip_text=tr("terminal_clear"))
        clr.add_css_class("flat")
        clr.add_css_class("term-btn")
        clr.connect("clicked", lambda *_: self.buf.set_text(""))
        close = Gtk.Button(icon_name="window-close-symbolic", tooltip_text=tr("close"))
        close.add_css_class("flat")
        close.add_css_class("term-btn")
        close.connect("clicked", lambda *_: on_close())
        head.append(clr)
        head.append(close)
        self.append(head)

        self.view = Gtk.TextView(editable=False, cursor_visible=False, monospace=True,
                                 wrap_mode=Gtk.WrapMode.WORD_CHAR, left_margin=10, right_margin=8, top_margin=6)
        self.view.add_css_class("term-text")
        self.buf = self.view.get_buffer()
        for name, col in COLORS.items():
            self.buf.create_tag(name, foreground=col)
        self.sc = Gtk.ScrolledWindow(child=self.view, vexpand=True)
        self.append(self.sc)

        self.prompt = Gtk.Label(xalign=0)
        self.prompt.add_css_class("term-prompt")
        self.append(self.prompt)
        self._blink = True
        GLib.timeout_add(530, self._tick)
        self._tick()

        for line in L.add_listener(lambda line: GLib.idle_add(self._append, line)):
            self._append(line)

    def _tick(self):
        self._blink = not self._blink
        cur = "▍" if self._blink else " "
        self.prompt.set_markup(f'<span foreground="#3ddc84">pma@linux</span><span foreground="#c8d3f5">:</span>'
                               f'<span foreground="#00e5ff">~/mastering</span><span foreground="#c8d3f5">$ {cur}</span>')
        return True

    def _append(self, line):
        t, tag, level, msg = line
        end = self.buf.get_end_iter()
        self.buf.insert_with_tags_by_name(end, f"[{t}] ", "time")
        self.buf.insert_with_tags_by_name(self.buf.get_end_iter(), f"{tag}", "tag")
        self.buf.insert_with_tags_by_name(self.buf.get_end_iter(), " » ", "sep")
        self.buf.insert_with_tags_by_name(self.buf.get_end_iter(), msg + "\n", level if level in COLORS else "info")
        extra = self.buf.get_line_count() - MAX_LINES
        if extra > 0:
            self.buf.delete(self.buf.get_start_iter(), self.buf.get_iter_at_line(extra)[1])
        GLib.idle_add(self._scroll)
        return False

    def _scroll(self):
        adj = self.sc.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False
