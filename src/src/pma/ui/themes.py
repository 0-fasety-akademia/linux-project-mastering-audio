"""Motywy wyglądu: Systemowy (Adwaita) oraz trzy własne – Neon Studio, Hologram, Konsola analogowa.
Kolory Adwaity są nadpisywane w osobnym dostawcy CSS (zmiana na żywo, bez restartu).
libadwaita ≥ 1.6 czyta zmienne CSS (--window-bg-color), starsze – @define-color, więc
blok kolorów jest generowany dla wersji, na której aplikacja działa."""
import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk  # noqa: E402

ORDER = ["system", "neon", "holo", "analog", "pro"]
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes")

# kolory Adwaity nadpisywane przez motyw
COLORS = {
    "neon": dict(window_bg="#0b0d1a", window_fg="#e8eaff", view_bg="#0f1224", view_fg="#e8eaff",
                 headerbar_bg="#0b0d1a", headerbar_fg="#e8eaff", card_bg="rgba(255,255,255,0.045)",
                 card_fg="#e8eaff", popover_bg="#151933", popover_fg="#e8eaff", dialog_bg="#151933",
                 dialog_fg="#e8eaff", accent_bg="#8b5cff", accent_fg="#ffffff", accent="#a98bff"),
    "holo": dict(window_bg="#030b14", window_fg="#bff4ff", view_bg="#04111d", view_fg="#bff4ff",
                 headerbar_bg="#030b14", headerbar_fg="#7fe9ff", card_bg="rgba(46,230,255,0.05)",
                 card_fg="#bff4ff", popover_bg="#061826", popover_fg="#bff4ff", dialog_bg="#061826",
                 dialog_fg="#bff4ff", accent_bg="#00b8d9", accent_fg="#001018", accent="#2ee6ff"),
    # Studio Pro: ergonomia długiej pracy – bez czystej czerni/bieli, hierarchia tłem zamiast ramek,
    # jeden przygaszony akcent (bursztyn), stonowane kolory mierników
    "pro": dict(window_bg="#1E1F22", window_fg="#E0E2E6", view_bg="#1A1B1E", view_fg="#E0E2E6",
                headerbar_bg="#1A1B1E", headerbar_fg="#D4D7DD", card_bg="#25272C", card_fg="#E0E2E6",
                popover_bg="#2E3138", popover_fg="#E0E2E6", dialog_bg="#2E3138", dialog_fg="#E0E2E6",
                accent_bg="#D99B26", accent_fg="#1A1B1E", accent="#D99B26"),
    "analog": dict(window_bg="#1d1b18", window_fg="#efe3c8", view_bg="#24211d", view_fg="#efe3c8",
                   headerbar_bg="#26231f", headerbar_fg="#e6d6b0", card_bg="#2a2722", card_fg="#efe3c8",
                   popover_bg="#2a2722", popover_fg="#efe3c8", dialog_bg="#2a2722", dialog_fg="#efe3c8",
                   accent_bg="#ffb547", accent_fg="#2a1d05", accent="#ffb547"),
}

# barwy rysowane w Cairo (wykres płyty, miernik A/B); RGB 0–1
PALETTE = {
    "system": dict(before=None, after=[(0.208, 0.518, 0.894)], target=(0.902, 0.380, 0.0), font="Sans",
                   radius=3.0, glow=False, meter="bar"),
    "neon": dict(before=(1, 1, 1, 0.14), after=[(0.18, 0.90, 1.0), (0.545, 0.36, 1.0), (1.0, 0.243, 0.647)],
                 target=(1.0, 0.61, 0.24), font="Sans", radius=7.0, glow=True, meter="neon"),
    "holo": dict(before=(0.18, 0.90, 1.0, 0.18), after=[(0.18, 0.90, 1.0)], target=(1.0, 0.82, 0.40),
                 font="Monospace", radius=0.0, glow=True, meter="segments"),
    "analog": dict(before=(0.94, 0.89, 0.78, 0.16), after=[(1.0, 0.71, 0.28)], target=(0.85, 0.27, 0.20),
                   font="Sans", radius=2.0, glow=False, meter="vu"),
    "pro": dict(before=(0.878, 0.886, 0.902, 0.10), after=[(0.851, 0.608, 0.149)], target=(0.231, 0.604, 0.698),
                font="Sans", radius=2.0, glow=False, meter="zones", outline=True, tnum=True,
                grid=(0.220, 0.235, 0.267), label=(0.541, 0.561, 0.596)),
}

CURRENT = "system"
_provider = None
_listeners = []


def palette():
    return PALETTE[CURRENT]


def on_change(cb):
    """cb() wołane po każdej zmianie motywu (np. przerysowanie wykresu)."""
    _listeners.append(cb)


def _color_block(c):
    if (Adw.get_major_version(), Adw.get_minor_version()) >= (1, 6):
        body = "".join(f"  --{k.replace('_', '-')}-color: {v};\n" for k, v in c.items())
        return ":root {\n" + body + "}\n"
    return "".join(f"@define-color {k}_color {v};\n" for k, v in c.items())


def css_for(key):
    if key not in COLORS:
        return ""
    with open(os.path.join(DIR, f"{key}.css"), encoding="utf-8") as f:
        extra = f.read()
    return _color_block(COLORS[key]) + "\n" + extra


def apply(key):
    global CURRENT, _provider
    key = key if key in ORDER else "system"
    display = Gdk.Display.get_default()
    if _provider is not None:
        Gtk.StyleContext.remove_provider_for_display(display, _provider)
        _provider = None
    sm = Adw.StyleManager.get_default()
    if key != "system":
        _provider = Gtk.CssProvider()
        _provider.load_from_string(css_for(key)) if hasattr(_provider, "load_from_string") \
            else _provider.load_from_data(css_for(key), -1)
        Gtk.StyleContext.add_provider_for_display(display, _provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    else:
        sm.set_color_scheme(Adw.ColorScheme.DEFAULT)
    CURRENT = key
    for cb in list(_listeners):
        try:
            cb()
        except Exception as e:  # noqa: BLE001
            print("theme listener:", e)
