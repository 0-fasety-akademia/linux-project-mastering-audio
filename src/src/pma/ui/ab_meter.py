"""Miernik szczytu w odsłuchu A/B, rysowany w stylu motywu:
pasek (Systemowy), świecący gradient (Neon Studio), segmenty HUD (Hologram), wskazówka VU (Konsola)."""
import math
import time

import gi

gi.require_version("Gtk", "4.0")
import cairo  # noqa: E402
from gi.repository import GLib, Gtk  # noqa: E402

from . import themes  # noqa: E402

FLOOR = -48.0
FALL_DB_S = 24.0          # opadanie wskazania (dB/s), jak w miernikach sprzętowych


def _frac(db):
    return max(0.0, min(1.0, (db - FLOOR) / -FLOOR))


class ABMeter(Gtk.DrawingArea):
    def __init__(self):
        super().__init__(hexpand=True)
        self.value = FLOOR
        self.hold = (FLOOR, 0.0)
        self._t = time.monotonic()
        self.set_draw_func(self._draw)
        themes.on_change(self._restyle)
        self._restyle()
        GLib.timeout_add(33, self._tick)

    def _restyle(self):
        kind = themes.palette()["meter"]
        self.set_content_height(118 if kind == "vu" else 38 if kind == "zones" else 34)
        self.queue_draw()

    def set_level(self, db):
        if db > self.value:
            self.value = db
        if db > self.hold[0] or time.monotonic() - self.hold[1] > 1.5:
            self.hold = (db, time.monotonic())

    def reset(self):
        self.value, self.hold = FLOOR, (FLOOR, 0.0)
        self.queue_draw()

    def _tick(self):
        now = time.monotonic()
        dt, self._t = now - self._t, now
        if self.value > FLOOR:
            self.value = max(FLOOR, self.value - FALL_DB_S * dt)
        self.queue_draw()
        return True

    # ---------------------------------------------------------------- rysowanie
    @staticmethod
    def _rr(cr, x, y, w, h, r):
        r = min(r, h / 2, w / 2)
        if w <= 0:
            return
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def _draw(self, _a, cr, w, h):
        kind = themes.palette()["meter"]
        getattr(self, "_draw_" + kind)(cr, w, h)

    def _fg(self, cr, a):
        c = self.get_color()
        cr.set_source_rgba(c.red, c.green, c.blue, a)

    def _draw_bar(self, cr, w, h):
        y, bh = (h - 10) / 2, 10
        self._fg(cr, 0.12)
        self._rr(cr, 0, y, w, bh, 5)
        cr.fill()
        c = themes.palette()["after"][0]
        cr.set_source_rgba(*c, 1)
        self._rr(cr, 0, y, w * _frac(self.value), bh, 5)
        cr.fill()
        self._hold_tick(cr, w, y, bh, (*c, 1))

    def _hold_tick(self, cr, w, y, bh, rgba):
        if self.hold[0] > FLOOR + 1:
            cr.set_source_rgba(*rgba)
            cr.rectangle(w * _frac(self.hold[0]) - 2, y - 2, 2, bh + 4)
            cr.fill()

    def _draw_neon(self, cr, w, h):
        y, bh = (h - 12) / 2, 12
        cr.set_source_rgba(1, 1, 1, 0.07)
        self._rr(cr, 0, y, w, bh, 6)
        cr.fill()
        fw = w * _frac(self.value)
        g = cairo.LinearGradient(0, 0, w, 0)
        for i, c in enumerate(themes.palette()["after"]):
            g.add_color_stop_rgba(i / 2, *c, 1)
        for grow, a in ((6, 0.10), (3, 0.18)):
            cr.set_source_rgba(0.545, 0.36, 1.0, a)
            self._rr(cr, -grow / 2, y - grow, fw + grow, bh + 2 * grow, 6 + grow)
            cr.fill()
        cr.set_source(g)
        self._rr(cr, 0, y, fw, bh, 6)
        cr.fill()
        self._hold_tick(cr, w, y, bh, (1, 1, 1, 0.9))

    def _draw_segments(self, cr, w, h):
        n, gap = 40, 3
        sw = (w - gap * (n - 1)) / n
        lit = round(n * _frac(self.value))
        hold = round(n * _frac(self.hold[0]))
        y, bh = (h - 16) / 2, 16
        for i in range(n):
            frac = (i + 1) / n
            c = (1.0, 0.33, 0.33) if frac > 0.94 else (1.0, 0.82, 0.40) if frac > 0.82 else (0.18, 0.90, 1.0)
            on = i < lit or i == hold - 1
            x = i * (sw + gap)
            if on:
                cr.set_source_rgba(*c, 0.25)
                cr.rectangle(x - 1.5, y - 2, sw + 3, bh + 4)
                cr.fill()
            cr.set_source_rgba(*c, 0.95 if on else 0.10)
            cr.rectangle(x, y, sw, bh)
            cr.fill()

    def _draw_zones(self, cr, w, h):
        """Studio Pro: płaski pasek, stonowane strefy – zieleń (bezpiecznie), bursztyn (uwaga),
        czerwień tylko przy samej górze skali; podziałka z opisem w szarości."""
        bh, y = 12, 4
        cr.set_source_rgb(0.180, 0.192, 0.220)           # #2E3138
        self._rr(cr, 0, y, w, bh, 3)
        cr.fill()
        zones = ((FLOOR, -12.0, (0.298, 0.651, 0.420)), (-12.0, -3.0, (0.851, 0.627, 0.212)),
                 (-3.0, 0.0, (0.839, 0.271, 0.271)))
        v = self.value
        cr.save()
        self._rr(cr, 0, y, w, bh, 3)
        cr.clip()
        for lo, hi, c in zones:
            if v <= lo:
                break
            x0, x1 = w * _frac(lo), w * _frac(min(v, hi))
            cr.set_source_rgb(*c)
            cr.rectangle(x0, y, x1 - x0, bh)
            cr.fill()
        cr.restore()
        if self.hold[0] > FLOOR + 1:
            cr.set_source_rgb(0.878, 0.886, 0.902)
            cr.rectangle(w * _frac(self.hold[0]) - 1, y - 2, 2, bh + 4)
            cr.fill()
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(10)
        for db in (-36, -24, -18, -12, -6, -3, 0):
            x = w * _frac(db)
            cr.set_source_rgb(0.220, 0.235, 0.267)       # #383C44
            cr.rectangle(round(x) - 0.5, y + bh + 2, 1, 4)
            cr.fill()
            lab = str(abs(db)) if db else "0"
            ext = cr.text_extents(lab)
            cr.set_source_rgb(0.541, 0.561, 0.596)       # #8A8F98
            cr.move_to(min(max(0, x - ext.width / 2), w - ext.width), y + bh + 16)
            cr.show_text(lab)

    def _draw_vu(self, cr, w, h):
        pw = min(w, 300.0)
        x0 = (w - pw) / 2
        g = cairo.RadialGradient(x0 + pw / 2, h * 1.25, 10, x0 + pw / 2, h * 1.25, pw * 0.9)
        g.add_color_stop_rgb(0, 1.0, 0.953, 0.81)
        g.add_color_stop_rgb(1, 0.949, 0.835, 0.553)
        cr.set_source(g)
        self._rr(cr, x0, 0, pw, h, 10)
        cr.fill()
        cx, cy = x0 + pw / 2, h + 34
        rs = cy - 24                                  # promień skali (łuk ~24 px od góry panelu)
        a0, a1 = math.radians(-138), math.radians(-42)
        cr.save()
        self._rr(cr, x0, 0, pw, h, 10)
        cr.clip()
        cr.set_line_width(1.6)
        cr.set_source_rgb(0.23, 0.18, 0.11)
        cr.arc(cx, cy, rs, a0, a1)
        cr.stroke()
        red0 = a0 + (a1 - a0) * _frac(-6.0)
        cr.set_line_width(5)
        cr.set_source_rgb(0.75, 0.22, 0.17)
        cr.arc(cx, cy, rs + 3, red0, a1)
        cr.stroke()
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(9.5)
        for db, lab in ((-40, "40"), (-30, "30"), (-20, "20"), (-12, "12"), (-6, "6"), (0, "0")):
            a = a0 + (a1 - a0) * _frac(db)
            red = db >= -6
            cr.set_source_rgb(0.75, 0.22, 0.17) if red else cr.set_source_rgb(0.23, 0.18, 0.11)
            cr.set_line_width(1.3)
            cr.move_to(cx + rs * math.cos(a), cy + rs * math.sin(a))
            cr.line_to(cx + (rs - 9) * math.cos(a), cy + (rs - 9) * math.sin(a))
            cr.stroke()
            ext = cr.text_extents(lab)
            tx, ty = cx + (rs - 19) * math.cos(a), cy + (rs - 19) * math.sin(a)
            cr.move_to(tx - ext.width / 2 - ext.x_bearing, ty - ext.height / 2 - ext.y_bearing)
            cr.show_text(lab)
        # wskazówka (z cieniem) i oś
        a = a0 + (a1 - a0) * _frac(self.value)
        for off, col in ((2.0, (0, 0, 0, 0.18)), (0.0, (0.11, 0.086, 0.063, 1))):
            cr.set_source_rgba(*col)
            cr.set_line_width(1.8)
            cr.move_to(cx + off, cy)
            cr.line_to(cx + off + (rs + 6) * math.cos(a), cy + (rs + 6) * math.sin(a))
            cr.stroke()
        cr.restore()
        cr.set_source_rgb(0.23, 0.18, 0.11)
        cr.select_font_face("Sans", 0, 1)
        cr.set_font_size(12)
        cr.move_to(cx - 10, h - 14)
        cr.show_text("VU")
        cr.set_source_rgba(0.24, 0.22, 0.19, 1)
        cr.set_line_width(3)
        self._rr(cr, x0 + 1.5, 1.5, pw - 3, h - 3, 9)
        cr.stroke()
