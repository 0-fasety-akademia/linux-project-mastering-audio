"""Przełącza ikonę aplikacji (menu, dock, okno) między wersją ciemną i jasną
zgodnie z motywem systemu – działa z autostartu, także gdy aplikacja jest zamknięta.

  python3 -m pma.iconsync          # jednorazowo
  python3 -m pma.iconsync --watch  # nasłuchuje zmian motywu (autostart)
"""
import os
import shutil
import sys

from . import APP_ID, paths

HOME = os.path.expanduser("~")
USER_ICON = os.path.join(HOME, ".local/share/icons/hicolor/scalable/apps", APP_ID + ".svg")
USER_DESKTOP = os.path.join(HOME, ".local/share/applications", APP_ID + ".desktop")
SYSTEM_DESKTOP = os.path.join("/usr/share/applications", APP_ID + ".desktop")


def variant_path(variant):
    return paths.data("icons", f"app-{variant}.svg")


def current_variant():
    try:
        from gi.repository import Gio
        src = Gio.SettingsSchemaSource.get_default()
        if src and src.lookup("org.gnome.desktop.interface", True):
            s = Gio.Settings.new("org.gnome.desktop.interface")
            if s.get_string("color-scheme") == "prefer-dark":
                return "dark"
            if "dark" in s.get_string("gtk-theme").lower() and s.get_string("color-scheme") == "default":
                return "dark"
            return "light"
    except Exception:  # noqa: BLE001
        pass
    return "dark"


def _write_if_changed(path, data):
    try:
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
    return True


def apply(variant=None):
    if not os.path.exists(SYSTEM_DESKTOP):
        # aplikacja odinstalowana – sprzątamy nadpisania użytkownika
        for p in (USER_ICON, USER_DESKTOP):
            if os.path.exists(p):
                os.remove(p)
        return None
    variant = variant or current_variant()
    src = variant_path(variant)
    with open(src, "rb") as f:
        icon = f.read()
    changed = _write_if_changed(USER_ICON, icon)
    with open(SYSTEM_DESKTOP) as f:
        lines = [(f"Icon={src}" if ln.startswith("Icon=") else ln) for ln in f.read().splitlines()]
    changed |= _write_if_changed(USER_DESKTOP, ("\n".join(lines) + "\n").encode())
    if changed:
        for d in (os.path.dirname(os.path.dirname(os.path.dirname(USER_ICON))), os.path.dirname(USER_DESKTOP)):
            try:
                os.utime(d, None)
            except OSError:
                pass
        if shutil.which("update-desktop-database"):
            os.system(f"update-desktop-database -q '{os.path.dirname(USER_DESKTOP)}' >/dev/null 2>&1")
    return variant


def watch():
    from gi.repository import Gio, GLib
    apply()
    src = Gio.SettingsSchemaSource.get_default()
    if not (src and src.lookup("org.gnome.desktop.interface", True)):
        return
    s = Gio.Settings.new("org.gnome.desktop.interface")
    s.connect("changed::color-scheme", lambda *_: apply())
    s.connect("changed::gtk-theme", lambda *_: apply())
    GLib.MainLoop().run()


if __name__ == "__main__":
    watch() if "--watch" in sys.argv else print(apply())
