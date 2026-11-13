"""Wykres płyty: głośność (LUFS) każdego utworu przed i po normalizacji, linia celu i LRA."""
import math

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("PangoCairo", "1.0")
import cairo  # noqa: E402
from gi.repository import Pango, PangoCairo, Gtk  # noqa: E402

from ..i18n import num, tr  # noqa: E402
from . import themes  # noqa: E402



def _minus(s):
    return s.replace("-", "−")


class AlbumChart(Gtk.DrawingArea):
    def __init__(self):
        super().__init__(hexpand=True)
        self.set_content_height(240)
        self.items = []          # dict(n, before, after, lra_before, lra_after)
        self.target = None
        self.measured = False
        self.set_draw_func(self._draw)
        themes.on_change(self.queue_draw)

    def set_data(self, items, target, measured):
        self.items, self.target, self.measured = items, target, measured
        self.queue_draw()

    # ---------------------------------------------------------------- rysowanie
    def _layout(self, cr, s, size, bold):
        lay = PangoCairo.create_layout(cr)
        fam = themes.palette()["font"]
        fd = Pango.FontDescription.from_string(f"{fam} {'Bold ' if bold else ''}{size * 0.75:.1f}")
        lay.set_font_description(fd)
        lay.set_text(s, -1)
        return lay

    def _text(self, cr, x, y, s, size=11, align="left", alpha=1.0, bold=False, rgb=None):
        """y = linia bazowa tekstu."""
        lay = self._layout(cr, s, size, bold)
        w, _h = lay.get_pixel_size()
        base = lay.get_baseline() / Pango.SCALE
        dx = {"left": 0, "center": -w / 2, "right": -w}[align]
        cr.move_to(x + dx, y - base)
        if rgb:
            cr.set_source_rgba(*rgb, alpha)
        else:
            self._fg(cr, alpha)
        PangoCairo.show_layout(cr, lay)
        return w

    def _fg(self, cr, alpha):
        c = self.get_color()
        cr.set_source_rgba(c.red, c.green, c.blue, alpha)

    @staticmethod
    def _bar(cr, x, y0, y1, w, r=3.0):
        h = y0 - y1
        if h <= 0:
            return
        r = min(r, w / 2, h)
        cr.new_sub_path()
        cr.arc(x + w - r, y1 + r, r, -math.pi / 2, 0)
        cr.line_to(x + w, y0)
        cr.line_to(x, y0)
        cr.arc(x + r, y1 + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()
        cr.fill()

    def _before_src(self, cr):
        b = themes.palette()["before"]
        if b:
            cr.set_source_rgba(*b)
        else:
            self._fg(cr, 0.28)

    def _after_src(self, cr, y_top, y_bottom):
        cols = themes.palette()["after"]
        a = 1.0 if self.measured else 0.55
        if len(cols) == 1:
            cr.set_source_rgba(*cols[0], a)
            return
        g = cairo.LinearGradient(0, y_bottom, 0, y_top)
        for i, c in enumerate(cols):
            g.add_color_stop_rgba(i / (len(cols) - 1), *c, a)
        cr.set_source(g)

    def _after_bar(self, cr, x, base, top, bw, r):
        pal = themes.palette()
        if pal["glow"] and self.measured:
            c = pal["after"][len(pal["after"]) // 2]
            for grow, alpha in ((7, 0.07), (4, 0.10), (2, 0.14)):
                cr.set_source_rgba(*c, alpha)
                self._bar(cr, x - grow, base, top - grow, bw + 2 * grow, r + grow)
        self._after_src(cr, top, base)
        self._bar(cr, x, base, top, bw, r)

    def _draw(self, _area, cr, w, h):
        if not self.items:
            return
        pal = themes.palette()
        radius = pal["radius"]
        left, right, top, bottom = 46, 14, 30, 40
        pw, ph = w - left - right, h - top - bottom
        vals = [v for it in self.items for v in (it["before"], it["after"])]
        if self.target is not None:
            vals.append(self.target)
        lo, hi = math.floor(min(vals) - 2), math.ceil(max(vals) + 1)
        if hi - lo < 8:
            lo = hi - 8
        step = 2 if hi - lo <= 16 else 5

        def Y(v):
            return top + (hi - v) / (hi - lo) * ph

        # siatka
        cr.set_line_width(1)
        v = math.ceil(lo / step) * step
        while v <= hi:
            self._fg(cr, 0.10)
            cr.move_to(left, round(Y(v)) + 0.5)
            cr.line_to(w - right, round(Y(v)) + 0.5)
            cr.stroke()
            self._text(cr, left - 8, Y(v) + 4, _minus(f"{v:d}"), 10, "right", 0.55)
            v += step
        self._text(cr, left - 8, top - 12, "LUFS", 10, "right", 0.55)

        # słupki
        n = len(self.items)
        gw = pw / n
        bw = max(4.0, min(26.0, gw * 0.33))
        base = Y(lo)
        for i, it in enumerate(self.items):
            cx = left + gw * (i + 0.5)
            self._before_src(cr)
            self._bar(cr, cx - bw - 1.5, base, Y(it["before"]), bw, radius)
            self._after_bar(cr, cx + 1.5, base, Y(it["after"]), bw, radius)
            self._text(cr, cx, h - bottom + 16, f"{it['n']:02d}", 11, "center", 0.8, bold=True)
            if gw >= 64:
                lra = f"LRA {num(it['lra_before'])}→{num(it['lra_after'])}" if self.measured \
                    else f"LRA {num(it['lra_before'])}"
                self._text(cr, cx, h - bottom + 31, lra, 9.5, "center", 0.55)

        # linia celu
        if self.target is not None:
            y = round(Y(self.target)) + 0.5
            cr.set_source_rgba(*pal["target"], 0.9)
            cr.set_line_width(1.5)
            cr.set_dash([6, 4])
            cr.move_to(left, y)
            cr.line_to(w - right, y)
            cr.stroke()
            cr.set_dash([])
            label = f"{tr('chart_target')} {_minus(num(self.target))}"
            self._text(cr, w - right, y - 5, label, 10, "right", 1.0, bold=True, rgb=pal["target"])

        # legenda
        x = left
        for kind, label in (("before", tr("chart_before")),
                            ("after", tr("chart_after") if self.measured else tr("chart_pred"))):
            if kind == "before":
                self._before_src(cr)
            else:
                self._after_src(cr, 9, 20)
            cr.rectangle(x, 9, 11, 11)
            cr.fill()
            x += 16 + self._text(cr, x + 16, 19, label, 11, "left", 0.8) + 18
