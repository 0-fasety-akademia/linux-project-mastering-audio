"""Dziennik zdarzeń dla mini-terminala.

W procesie GUI log() trafia od razu do słuchaczy (terminal).
W procesach roboczych log() wysyła linię kolejką do GUI (kolejka ustawiana
przez initializer puli procesów)."""
import os
import threading
import time

_queue = None
_listeners = []
_history = []
_lock = threading.Lock()
MAX_HISTORY = 400


def init_worker(q):
    global _queue
    _queue = q


def log(msg, level="info", tag=None):
    line = (time.strftime("%H:%M:%S"), tag or f"pid {os.getpid()}", level, str(msg))
    if _queue is not None:
        try:
            _queue.put_nowait(line)
        except Exception:  # noqa: BLE001
            pass
    else:
        emit(line)


def emit(line):
    with _lock:
        _history.append(line)
        del _history[:-MAX_HISTORY]
        listeners = list(_listeners)
    for cb in listeners:
        cb(line)


def add_listener(cb):
    with _lock:
        _listeners.append(cb)
        return list(_history)


def start_reader(q):
    """Wątek w procesie GUI przepisujący linie z procesów roboczych."""
    def run():
        while True:
            try:
                line = q.get()
            except (EOFError, OSError):
                return
            if line is None:
                return
            emit(line)
    threading.Thread(target=run, daemon=True, name="pma-log-reader").start()
