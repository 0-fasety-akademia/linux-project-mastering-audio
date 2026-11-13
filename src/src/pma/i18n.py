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
        "a_norm_sub": "Równy poziom całej płyty i ochrona przed przesterem",
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
        "report_target": "Cel: {target}; sposób: {mode}; limit szczytu {ceil:.1f} dBTP",
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
        "a_norm_sub": "Even level across the whole album and protection against clipping",
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
        "report_target": "Target: {target}; method: {mode}; peak ceiling {ceil:.1f} dBTP",
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


# 0.3.0: mastering miksu, pułap zależny od celu, wykres płyty, odsłuch A/B
S["pl"].update({
    "a_master": "Mastering miksu",
    "a_master_sub": "Opcjonalnie: lekka obróbka całego utworu przed normalizacją",
    "master_style": "Charakter",
    "mp_off": "Bez masteringu",
    "mp_off_d": "Tylko normalizacja – brzmienie bez zmian",
    "mp_gentle": "Delikatny",
    "mp_gentle_d": "Lekkie sklejenie miksu i odrobina powietrza",
    "mp_warm": "Ciepły",
    "mp_warm_d": "Pełniejszy dół, łagodniejsza góra, nasycenie",
    "mp_modern": "Nowoczesny",
    "mp_modern_d": "Czysty środek, więcej obecności i blasku",
    "mp_punch": "Mocny",
    "mp_punch_d": "Wyraźny dół i atak, mocniejsza kompresja",
    "ceiling_info": "Limit szczytów {ceil:.1f} dBTP",
    "ceiling_info_loud": "Limit szczytów {ceil:.1f} dBTP (głośny master)",
    "report_master": "Mastering: {name}",
    "col_limiter": "Limiter",
    "report_squash": "UWAGA: w utworach {tracks} limiter ściął szczyty o ponad {db:.0f} dB – mogą brzmieć płasko. "
                     "Rozważ niższy poziom docelowy albo tryb „Jedno wzmocnienie dla płyty”.",
    "report_lra": "LRA = zakres dynamiki (EBU R128) przed > po; im mniejszy, tym bardziej ściśnięty utwór.",
    "report_limiter": "Limiter = o ile dB ścięto najwyższy szczyt; powyżej 3 dB utwór może brzmieć płasko (!).",
    "warn_squash": "\n\n⚠ W utworach {tracks} limiter mocno ściął szczyty – szczegóły w raporcie.",
    "chart_title": "Płyta w liczbach",
    "chart_sub": "Głośność utworów przed i po (LUFS) oraz zakres dynamiki (LRA)",
    "chart_before": "przed",
    "chart_after": "po",
    "chart_pred": "po (przewidywane)",
    "chart_target": "cel",
    "ab_title": "Odsłuch A/B",
    "ab_sub": "Oryginał i wynik grają z tą samą głośnością – słychać tylko różnicę brzmienia",
    "ab_track": "Utwór",
    "ab_a": "A · oryginał",
    "ab_b": "B · po",
    "ab_matched": "Obie wersje wyrównane do {lufs:.1f} LUFS",
    "theme": "Motyw",
    "a_tracks_sub": "Kolejność według nazw plików – przeciągnij, aby dodać kolejne",
    "tshort_streaming": "Streaming · −14 LUFS",
    "tshort_apple": "Apple Music · −16 LUFS",
    "tshort_cd": "CD / sklep · −10 LUFS",
    "tshort_loud": "Głośno · −8 LUFS",
    "tshort_manual": "Własny",
    "tdesc_streaming": "Spotify, YouTube, Tidal, Amazon",
    "tdesc_apple": "Apple Music / iTunes Sound Check",
    "tdesc_cd": "Płyta CD i pliki „jak ze sklepu”",
    "tdesc_loud": "Klub, rap, EDM – bardzo głośno",
    "tdesc_manual": "MANUAL – wartość wpisana poniżej",
    "target_manual": "Własny poziom ({lufs:.1f} LUFS)",
    "manual_lufs": "Własny poziom (LUFS)",
    "manual_hint": "Od −30 do −5. Typowo: streaming −14 · Apple −16 · CD −9…−12 · klub −6…−8. Im głośniej, tym mniej dynamiki.",
    "mshort_loud_parts": "Równe refreny",
    "mshort_integrated": "Równa średnia",
    "mshort_album_gain": "Jedno wzmocnienie",
    "mdesc_loud_parts": "Zalecane – refreny równo głośne, zwrotki zachowują dynamikę",
    "mdesc_integrated": "Każdy utwór ma identyczną średnią głośność",
    "mdesc_album_gain": "Cała płyta podgłośniona tak samo – zostają różnice z miksu",
    "wshort_cd": "CD · 16 bit",
    "wshort_hires": "Hi-Res · 24 bit",
    "wdesc_cd": "44,1 kHz z ditherem – do wypalenia na płycie",
    "wdesc_hires": "Oryginalna częstotliwość próbkowania",
    "ab_m": "Chwilowa (400 ms)",
    "ab_s": "Krótkookresowa (3 s)",
    "ab_i": "Zintegrowana (cały utwór)",
    "ab_files": "Pliki: A {a:.1f} LUFS · B {b:.1f} LUFS – głośniejszą wersję ściszono o {d:.1f} dB, żeby porównanie było uczciwe",
    "ab_calc": "Liczenie głośności…",
    "vp_pop": "Pop",
    "vp_pop_d": "Jasny i do przodu, gęsta kompresja",
    "vp_acoustic": "Akustyczny",
    "vp_acoustic_d": "Naturalny, lekka kompresja, mała sala",
    "vp_rnb": "R&B / Soul",
    "vp_rnb_d": "Ciepły i gładki, długi pogłos z echem",
    "vp_podcast": "Mowa",
    "vp_podcast_d": "Podcast, lektor – sucho i wyraźnie",
    "vp_lofi": "Lo-fi",
    "vp_lofi_d": "Wąskie pasmo, nasycenie, vintage",
    "vp_manual": "MANUAL",
    "vp_manual_d": "Wszystko ustawiasz suwakami",
    "v_manual": "Mastering ręczny (MANUAL)",
    "v_manual_sub": "Działa na ścieżki z opcją MANUAL – zmiany słychać po ok. sekundzie",
    "mt_tone": "Barwa (EQ)",
    "mt_dyn": "Kompresja",
    "mt_clean": "De-esser i nasycenie",
    "mt_space": "Przestrzeń",
    "mk_lowcut": "Filtr dołu",
    "mk_body": "Ciało 200 Hz",
    "mk_mud": "Błoto 350 Hz",
    "mk_presence": "Obecność 3,5 kHz",
    "mk_air": "Powietrze 12 kHz",
    "mk_deess": "De-esser",
    "mk_comp_thr": "Próg",
    "mk_comp_ratio": "Stopień",
    "mk_attack": "Atak",
    "mk_release": "Powrót",
    "mk_saturation": "Nasycenie",
    "mk_reverb_size": "Pogłos",
    "mk_predelay": "Opóźnienie pogłosu",
    "mk_echo_ms": "Echo",
    "mk_echo_fb": "Powtórzenia echa",
    "mk_reset": "Przywróć ustawienia Studio",
    "off": "wył.",
    "theme_system": "Systemowy",
    "theme_neon": "Neon Studio",
    "theme_holo": "Hologram",
    "theme_analog": "Konsola analogowa",
})
S["en"].update({
    "a_master": "Mix mastering",
    "a_master_sub": "Optional: light processing of the whole track before normalization",
    "master_style": "Character",
    "mp_off": "No mastering",
    "mp_off_d": "Normalization only – sound unchanged",
    "mp_gentle": "Gentle",
    "mp_gentle_d": "Light glue and a touch of air",
    "mp_warm": "Warm",
    "mp_warm_d": "Fuller lows, softer highs, saturation",
    "mp_modern": "Modern",
    "mp_modern_d": "Clean mids, more presence and sparkle",
    "mp_punch": "Punchy",
    "mp_punch_d": "Solid low end and attack, firmer compression",
    "ceiling_info": "Peak ceiling {ceil:.1f} dBTP",
    "ceiling_info_loud": "Peak ceiling {ceil:.1f} dBTP (loud master)",
    "report_master": "Mastering: {name}",
    "col_limiter": "Limiter",
    "report_squash": "WARNING: in tracks {tracks} the limiter cut peaks by more than {db:.0f} dB – they may sound flat. "
                     "Consider a lower target or the “One gain for the whole album” method.",
    "report_lra": "LRA = loudness range (EBU R128) before > after; the smaller, the more squashed the track.",
    "report_limiter": "Limiter = how many dB the highest peak was cut; above 3 dB a track may sound flat (!).",
    "warn_squash": "\n\n⚠ In tracks {tracks} the limiter cut peaks hard – see the report.",
    "chart_title": "The album in numbers",
    "chart_sub": "Track loudness before and after (LUFS) and loudness range (LRA)",
    "chart_before": "before",
    "chart_after": "after",
    "chart_pred": "after (predicted)",
    "chart_target": "target",
    "ab_title": "A/B listening",
    "ab_sub": "Original and result play at the same loudness – you hear only the difference in sound",
    "ab_track": "Track",
    "ab_a": "A · original",
    "ab_b": "B · after",
    "ab_matched": "Both versions matched to {lufs:.1f} LUFS",
    "theme": "Theme",
    "a_tracks_sub": "Ordered by file name – drop more files to add them",
    "tshort_streaming": "Streaming · −14 LUFS",
    "tshort_apple": "Apple Music · −16 LUFS",
    "tshort_cd": "CD / store · −10 LUFS",
    "tshort_loud": "Loud · −8 LUFS",
    "tshort_manual": "Custom",
    "tdesc_streaming": "Spotify, YouTube, Tidal, Amazon",
    "tdesc_apple": "Apple Music / iTunes Sound Check",
    "tdesc_cd": "CD and “store-ready” files",
    "tdesc_loud": "Club, rap, EDM – very loud",
    "tdesc_manual": "MANUAL – the value typed below",
    "target_manual": "Custom level ({lufs:.1f} LUFS)",
    "manual_lufs": "Custom level (LUFS)",
    "manual_hint": "From −30 to −5. Typical: streaming −14 · Apple −16 · CD −9…−12 · club −6…−8. Louder means less dynamics.",
    "mshort_loud_parts": "Equal choruses",
    "mshort_integrated": "Equal average",
    "mshort_album_gain": "One album gain",
    "mdesc_loud_parts": "Recommended – choruses equally loud, verses keep their dynamics",
    "mdesc_integrated": "Every track gets the same average loudness",
    "mdesc_album_gain": "The whole album raised by the same amount – mix differences stay",
    "wshort_cd": "CD · 16 bit",
    "wshort_hires": "Hi-Res · 24 bit",
    "wdesc_cd": "44.1 kHz with dither – ready to burn",
    "wdesc_hires": "Original sample rate",
    "ab_m": "Momentary (400 ms)",
    "ab_s": "Short-term (3 s)",
    "ab_i": "Integrated (whole track)",
    "ab_files": "Files: A {a:.1f} LUFS · B {b:.1f} LUFS – the louder one is turned down by {d:.1f} dB for a fair comparison",
    "ab_calc": "Measuring loudness…",
    "vp_pop": "Pop",
    "vp_pop_d": "Bright and upfront, dense compression",
    "vp_acoustic": "Acoustic",
    "vp_acoustic_d": "Natural, light compression, small room",
    "vp_rnb": "R&B / Soul",
    "vp_rnb_d": "Warm and smooth, long reverb with echo",
    "vp_podcast": "Speech",
    "vp_podcast_d": "Podcast, voice-over – dry and clear",
    "vp_lofi": "Lo-fi",
    "vp_lofi_d": "Narrow band, saturation, vintage",
    "vp_manual": "MANUAL",
    "vp_manual_d": "You set everything with sliders",
    "v_manual": "Manual mastering (MANUAL)",
    "v_manual_sub": "Applies to tracks set to MANUAL – changes are heard after about a second",
    "mt_tone": "Tone (EQ)",
    "mt_dyn": "Compression",
    "mt_clean": "De-esser & saturation",
    "mt_space": "Space",
    "mk_lowcut": "Low cut",
    "mk_body": "Body 200 Hz",
    "mk_mud": "Mud 350 Hz",
    "mk_presence": "Presence 3.5 kHz",
    "mk_air": "Air 12 kHz",
    "mk_deess": "De-esser",
    "mk_comp_thr": "Threshold",
    "mk_comp_ratio": "Ratio",
    "mk_attack": "Attack",
    "mk_release": "Release",
    "mk_saturation": "Saturation",
    "mk_reverb_size": "Reverb",
    "mk_predelay": "Pre-delay",
    "mk_echo_ms": "Echo",
    "mk_echo_fb": "Echo repeats",
    "mk_reset": "Reset to Studio",
    "off": "off",
    "theme_system": "System",
    "theme_neon": "Neon Studio",
    "theme_holo": "Hologram",
    "theme_analog": "Analog console",
})


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
        if isinstance(value, float):
            out = out.replace("-", "−")          # typograficzny minus (−2,0 dBTP)
            if LANG == "pl":
                out = out.replace(".", ",")
        return out


_FMT = _Fmt()


def num(value, spec=".1f"):
    return _FMT.format_field(float(value), spec)


def tr(key, **kw):
    s = S[LANG].get(key) or S["en"].get(key) or key
    return _FMT.format(s, **kw) if kw else s
