import os

_here = os.path.dirname(os.path.abspath(__file__))
_candidates = [
    os.environ.get("PMA_DATA", ""),
    os.path.join(_here, "..", "..", "data"),                      # uruchomienie ze źródeł
    "/usr/share/linux-project-mastering-audio/data",              # zainstalowany .deb
]
DATA = next((os.path.abspath(p) for p in _candidates if p and os.path.isdir(p)), _candidates[-1])


def data(*parts):
    return os.path.join(DATA, *parts)
