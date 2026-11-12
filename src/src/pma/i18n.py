"""Proste tłumaczenia PL / EN."""
import json
import locale
import os
import string

CONFIG_DIR = os.path.join(os.path.expanduser("~/.config"), "linux-project-mastering-audio")
CONFIG = os.path.join(CONFIG_DIR, "settings.json")

S = {
    "pl": {
        # start
        "loading_engine": "Ładowanie silnika audio…",
        "loading_ui": "Przygotowywanie interfejsu…",
        "ready": "Gotowe",
        # wspólne
        "tab_vocal": "Wokal",
        "tab_album": "Album",
        "choose_files": "Wybierz pliki…",
        "add_files": "Dodaj pliki",
        "clear": "Wyczyść listę",
        "remove": "Usuń",
        "analyzing": "Analiza…",
        "rendering": "Przetwarzanie…",
        "analysis_failed": "Nie udało się wczytać pliku",
        "files_filter": "Pliki audio",
        "images_filter": "Obrazy PNG",
        "error": "Błąd",
        "close": "Zamknij",
        "cancel": "Anuluj",
        "open_folder": "Otwórz folder",
        "about": "O programie",
        "language": "Język",
        "quit": "Zakończ",
        "about_comments": "Mastering ścieżek wokalu i normalizacja głośności albumu.",
        "made_by": "made by: JGu",
        "supported_by": "Supported by Claude",
        "lang_restart": "Język zostanie zmieniony po ponownym uruchomieniu.",
        "quit_busy_title": "Praca w toku",
        "quit_busy_body": "Zamknięcie przerwie przetwarzanie. Zakończyć?",
        "play": "Odtwórz",
        "pause": "Pauza",
        # wokal
        "v_drop_title": "Przeciągnij ścieżki wokalu",
        "v_drop_sub": "1–10 plików WAV: wokal główny, dopowiedzi, chórki… – kolejność według nazw",
        "v_tracks": "Ścieżki wokalu",
        "v_style": "Mastering wokalu",
        "v_style_sub": "Wybór ustawia wszystkie ścieżki – każdą możesz potem zmienić osobno",
        "vp_studio": "Studio",
        "vp_radio": "Radio",
        "vp_warm": "Ciepły",
        "vp_space": "Przestrzeń",
        "vp_rap": "Rap",
        "vp_studio_d": "Czysty i przejrzysty, z delikatnym pogłosem",
        "vp_radio_d": "Wysunięty do przodu, jasny, z krótkim echem",
        "vp_warm_d": "Miękki i pełny, z aksamitnym pogłosem",
        "vp_space_d": "Dużo powietrza i długie echo",
        "vp_rap_d": "Twardy i wyraźny, sucho i blisko",
        "volume": "Głośność",
        "fx": "Pogłos / echo",
        "mute": "Wycisz",
        "listen": "Odsłuch na żywo",
        "listen_sub": "Suwaki działają w trakcie odtwarzania",
        "meter_ok": "Poziom OK",
        "meter_hot": "Za głośno – ścisz suwaki (wynik i tak zostanie zabezpieczony przed przesterem)",
        "merge": "Scal wszystkie ścieżki w jedną",
        "merging": "Scalanie ścieżek…",
        "merge_save_title": "Zapisz scalony wokal",
        "merge_done_title": "Wokal scalony",
        "merge_done_body": "Zapisano: {name}\n{lufs:.1f} LUFS · szczyt {tp:.1f} dBTP",
        "merge_limited": "\nSzczyty zabezpieczono limiterem ({db:.1f} dB).",
        "merged_suffix": "wokal_scalony",
        "count_dur": "{count} · {dur}",
        # album
        "a_drop_title": "Przeciągnij gotowe utwory albumu",
        "a_drop_sub": "Zmiksowane i zmasterowane WAV-y – kolejność według nazw plików",
        "a_tracks": "Utwory",
        "a_norm": "Normalizacja głośności",
        "a_norm_sub": "Bez zmiany brzmienia – tylko równy poziom całej płyty i ochrona przed przesterem",
        "target": "Poziom docelowy",
        "target_streaming": "Streaming – Spotify, YouTube (−14 LUFS)",
        "target_apple": "Apple Music (−16 LUFS)",
        "target_cd": "CD / sklep (−10 LUFS)",
        "target_loud": "Głośno – klub, rap (−8 LUFS)",
        "mode": "Sposób wyrównania",
        "mode_loud_parts": "Równe refreny (zalecane)",
        "mode_integrated": "Równa średnia głośność",
        "mode_album_gain": "Jedno wzmocnienie dla płyty (zachowaj różnice z miksu)",
        "track_meta": "{dur} · {lufs:.1f} LUFS · szczyt {tp:.1f} dBTP",
        "change": " → zmiana ≈ {db:+.1f} dB",
        "output": "Zapis",
        "wav_quality": "Jakość WAV",
        "wav_cd": "CD – 16 bit / 44,1 kHz",
        "wav_hires": "Hi-Res – 24 bit, oryginalna częstotliwość",
        "formats": "Formaty",
        "artist": "Wykonawca",
        "album": "Album",
        "cover": "Okładka (PNG)",
        "cover_none": "Brak – przeciągnij PNG lub kliknij",
        "cover_remove": "Usuń okładkę",
        "normalize": "Normalizuj cały album",
        "normalizing": "Normalizacja… {done}/{total}",
        "done_title": "Album gotowy",
        "done_body": "Zapisano {count} w folderze „normalized”.",
        "show_report": "Raport",
        "no_format": "Wybierz przynajmniej jeden format.",
        "notif_done": "Gotowe – {count}",
        "notif_merge": "Wokal scalony",
        "report_title": "Linux Project Mastering Audio – normalizacja albumu",
        "report_target": "Cel: {target}; sposób: {mode}; limit szczytu −1,0 dBTP",
        "col_track": "Utwór",
        "col_before": "Przed LUFS/TP",
        "col_after": "Po LUFS/TP",
        "col_chorus": "Refren",
        "report_chorus": "Refren = głośność głośnych fragmentów (95. percentyl short-term) przed > po; w trybie „Równe refreny” to ona jest wyrównywana.",
        "terminal": "Terminal – co się dzieje",
        "terminal_clear": "Wyczyść",
        "report_units": "LUFS = głośność zintegrowana (EBU R128), TP = true peak w dBTP.",
    },
    "en": {
        "loading_engine": "Loading audio engine…",
        "loading_ui": "Preparing interface…",
        "ready": "Ready",
        "tab_vocal": "Vocals",
        "tab_album": "Album",
        "choose_files": "Choose files…",
        "add_files": "Add files",
        "clear": "Clear list",
        "remove": "Remove",
        "analyzing": "Analyzing…",
        "rendering": "Processing…",
        "analysis_failed": "Could not read the file",
        "files_filter": "Audio files",
        "images_filter": "PNG images",
        "error": "Error",
        "close": "Close",
        "cancel": "Cancel",
        "open_folder": "Open folder",
        "about": "About",
        "language": "Language",
        "quit": "Quit",
        "about_comments": "Vocal track mastering and album loudness normalization.",
        "made_by": "made by: JGu",
        "supported_by": "Supported by Claude",
        "lang_restart": "The language will change after restarting the app.",
        "quit_busy_title": "Work in progress",
        "quit_busy_body": "Closing will stop processing. Quit anyway?",
        "play": "Play",
        "pause": "Pause",
        "v_drop_title": "Drop your vocal tracks",
        "v_drop_sub": "1–10 WAV files: lead vocal, ad-libs, backing vocals… – ordered by file name",
        "v_tracks": "Vocal tracks",
        "v_style": "Vocal mastering",
        "v_style_sub": "Sets all tracks – you can change each one separately afterwards",
        "vp_studio": "Studio",
        "vp_radio": "Radio",
        "vp_warm": "Warm",
        "vp_space": "Space",
        "vp_rap": "Rap",
        "vp_studio_d": "Clean, clear, subtle reverb",
        "vp_radio_d": "Upfront, bright, short echo",
        "vp_warm_d": "Soft, full, velvet reverb",
        "vp_space_d": "Lots of air, long echo",
        "vp_rap_d": "Hard, crisp, dry and close",
        "volume": "Volume",
        "fx": "Reverb / echo",
        "mute": "Mute",
        "listen": "Live listening",
        "listen_sub": "Sliders work while playing",
        "meter_ok": "Level OK",
        "meter_hot": "Too loud – lower the sliders (the result is clip-protected anyway)",
        "merge": "Merge all tracks into one",
        "merging": "Merging tracks…",
        "merge_save_title": "Save merged vocal",
        "merge_done_title": "Vocal merged",
        "merge_done_body": "Saved: {name}\n{lufs:.1f} LUFS · peak {tp:.1f} dBTP",
        "merge_limited": "\nPeaks were limited ({db:.1f} dB).",
        "merged_suffix": "vocal_merged",
        "count_dur": "{count} · {dur}",
        "a_drop_title": "Drop the finished album tracks",
        "a_drop_sub": "Mixed and mastered WAVs – ordered by file name",
        "a_tracks": "Tracks",
        "a_norm": "Loudness normalization",
        "a_norm_sub": "No change to the sound – just an even level across the album and clip protection",
        "target": "Target level",
        "target_streaming": "Streaming – Spotify, YouTube (−14 LUFS)",
        "target_apple": "Apple Music (−16 LUFS)",
        "target_cd": "CD / store (−10 LUFS)",
        "target_loud": "Loud – club, rap (−8 LUFS)",
        "mode": "Matching method",
        "mode_loud_parts": "Equal choruses (recommended)",
        "mode_integrated": "Equal average loudness",
        "mode_album_gain": "One gain for the whole album (keep mix differences)",
        "track_meta": "{dur} · {lufs:.1f} LUFS · peak {tp:.1f} dBTP",
        "change": " → change ≈ {db:+.1f} dB",
        "output": "Output",
        "wav_quality": "WAV quality",
        "wav_cd": "CD – 16 bit / 44.1 kHz",
        "wav_hires": "Hi-Res – 24 bit, original sample rate",
        "formats": "Formats",
        "artist": "Artist",
        "album": "Album",
        "cover": "Cover (PNG)",
        "cover_none": "None – drop a PNG or click",
        "cover_remove": "Remove cover",
        "normalize": "Normalize whole album",
        "normalizing": "Normalizing… {done}/{total}",
        "done_title": "Album ready",
        "done_body": "Saved {count} to the “normalized” folder.",
        "show_report": "Report",
        "no_format": "Choose at least one format.",
        "notif_done": "Done – {count}",
        "notif_merge": "Vocal merged",
        "report_title": "Linux Project Mastering Audio – album normalization",
        "report_target": "Target: {target}; method: {mode}; peak ceiling −1.0 dBTP",
        "col_track": "Track",
        "col_before": "Before LUFS/TP",
        "col_after": "After LUFS/TP",
        "col_chorus": "Chorus",
        "report_chorus": "Chorus = loudness of the loud parts (95th percentile short-term) before > after; “Equal choruses” mode matches this value.",
        "terminal": "Terminal – what's going on",
        "terminal_clear": "Clear",
        "report_units": "LUFS = integrated loudness (EBU R128), TP = true peak in dBTP.",
    },
}


def load_settings():
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def save_settings(d):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG, "w") as f:
        json.dump(d, f, indent=2)


def system_lang():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var, "")
        if v:
            return "pl" if v.lower().startswith("pl") else "en"
    try:
        return "pl" if (locale.getlocale()[0] or "").lower().startswith("pl") else "en"
    except Exception:  # noqa: BLE001
        return "en"


LANG = load_settings().get("language") or system_lang()
if LANG not in S:
    LANG = "en"


# ------------------------------------------------------------------ odmiana i liczby
WORDS = {
    "pl": {"song": ("utwór", "utwory", "utworów"), "stem": ("ścieżka", "ścieżki", "ścieżek")},
    "en": {"song": ("track", "tracks"), "stem": ("track", "tracks")},
}


def plural(n, kind, lang=None):
    """Poprawna forma: 1 utwór, 2–4 utwory, 5+ utworów (22 utwory, 12 utworów…); 1 track / 2 tracks."""
    lang = lang or LANG
    forms = WORDS.get(lang, WORDS["en"])[kind]
    n = abs(int(n))
    if lang == "pl":
        if n == 1:
            return forms[0]
        if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
            return forms[1]
        return forms[2]
    return forms[0] if n == 1 else forms[1]


def count(n, kind, lang=None):
    return f"{n} {plural(n, kind, lang)}"


class _Fmt(string.Formatter):
    """W polskiej wersji liczby dziesiętne z przecinkiem (−9,6 LUFS)."""

    def format_field(self, value, spec):
        out = super().format_field(value, spec)
        if LANG == "pl" and isinstance(value, float):
            out = out.replace(".", ",")
        return out


_FMT = _Fmt()


def num(value, spec=".1f"):
    return _FMT.format_field(float(value), spec)


def tr(key, **kw):
    s = S[LANG].get(key) or S["en"].get(key) or key
    return _FMT.format(s, **kw) if kw else s
