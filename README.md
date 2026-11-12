# linux-project-mastering-audio — Linux Project Mastering Audio

Prosta aplikacja na Ubuntu z dwiema zakładkami:

1. **Wokal** – mastering ścieżek wokalu (wokal główny, dopowiedzi, chórki…), odsłuch na żywo, suwaki
   głośności i pogłosu/echa dla każdej ścieżki i przycisk **SCAL WSZYSTKIE ŚCIEŻKI W JEDNĄ** → jeden końcowy WAV.
2. **Album** – gotowe, zmiksowane utwory: **normalizacja głośności całej płyty** (bez zmiany brzmienia)
   i przycisk **NORMALIZUJ CAŁY ALBUM**.

To nie jest drugi Audacity – tylko to, co potrzebne.

*English version below.*

---

## Zakładka WOKAL

1. Przeciągnij **1–10 plików WAV** (mono lub stereo; także FLAC/AIFF). Ścieżki dostają litery **A, B, C…** według nazw plików.
   Wszystkie powinny zaczynać się w tym samym momencie (tak jak eksportuje je DAW).
2. Wybierz **opcję masteringu** – kafelek ustawia wszystkie ścieżki, a przy każdej ścieżce możesz ją zmienić osobno:

   | Opcja | Charakter | Pogłos / echo (start) |
   |---|---|---|
   | **Studio** | czysty, przejrzysty | delikatny pogłos płytowy (15%) |
   | **Radio** | do przodu, jasny, mocniej skompresowany | krótkie echo „slap” + mały pogłos (20%) |
   | **Ciepły** | miękki, pełny, lekkie nasycenie | aksamitny, dłuższy pogłos (28%) |
   | **Przestrzeń** | dużo powietrza | duży pogłos + echo ping-pong (40%) |
   | **Rap** | twardy, wyraźny, blisko | sucho, bardzo krótkie echo (12%) |

   Każda opcja to: filtr dolnozaporowy, korekcja „błota” i obecności, **de-esser** (przycisza syczące s/sz/cz – dwa przebiegi),
   kompresja, nasycenie, blask w górze pasma, a efekt (pogłos/echo) jest wysyłany po filtrze, jak w profesjonalnym miksie.
3. Przy każdej ścieżce:
   - **Głośność** (−24…+12 dB),
   - **Pogłos / echo** (0–100%; 0 = bez efektu),
   - **Wycisz** (wyciszona ścieżka nie trafia do wyniku).
4. **Odsłuch na żywo** (pasek na dole): suwaki działają w trakcie odtwarzania, miernik pokazuje szczyt sumy
   i ostrzega, gdy jest za głośno.
5. **SCAL WSZYSTKIE ŚCIEŻKI W JEDNĄ** – wybierasz nazwę pliku i dostajesz **jeden WAV 24-bit** (częstotliwość
   pierwszej ścieżki). Wynik brzmi dokładnie tak jak odsłuch. Jeśli suma przekroczy −1 dBTP, szczyty zabezpiecza limiter.

Przetworzone ścieżki są zapamiętywane w `~/.cache/linux-project-mastering-audio/vocal/`, więc powrót do opcji, którą
już słuchałeś, jest natychmiastowy (cache można bezpiecznie usuwać).

## Zakładka ALBUM

1. Przeciągnij gotowe utwory (kolejność = nazwy plików). Przy każdym widać głośność (LUFS), szczyt (dBTP)
   i **przewidywaną zmianę** dla wybranych ustawień.
2. **Poziom docelowy:**
   - Streaming – Spotify, YouTube (−14 LUFS)
   - Apple Music (−16 LUFS)
   - CD / sklep (−10 LUFS)
   - Głośno – klub, rap (−8 LUFS)
3. **Sposób wyrównania:**
   - **Równe refreny (zalecane)** – głośne fragmenty wszystkich utworów na tym samym poziomie; spokojne zwrotki zachowują dynamikę,
   - **Równa średnia głośność** – identyczny LUFS każdego utworu,
   - **Jedno wzmocnienie dla płyty** – najgłośniejszy utwór trafia w cel, reszta dostaje to samo wzmocnienie (zachowuje różnice z miksu).
4. **Zapis:** WAV (CD 16 bit/44,1 kHz z ditherem albo Hi-Res 24 bit), MP3 320 kbps, MP4 (AAC 256 kbps, koder FDK) –
   z okładką PNG i tagami (tytuł z nazwy pliku, wykonawca, album, numer).
5. **NORMALIZUJ CAŁY ALBUM** → folder **`normalized/`** obok oryginałów + `raport.txt` (przed/po, łącznie z poziomem refrenu).

Brzmienie się nie zmienia: tylko wzmocnienie + ochrona szczytów (miękki clipper i limiter true-peak −1,0 dBTP).
MP3 i MP4 są sprawdzane **po zakodowaniu** i w razie przesteru automatycznie poprawiane.

## Mini-terminal

Przycisk z ikoną terminala w pasku tytułu (prawy górny róg) włącza małe okienko terminala, które na żywo pokazuje,
co robi silnik: wczytywanie i pomiary (LUFS, true peak), kolejne etapy obróbki wokalu (filtr, EQ, de-esser, kompresja,
pogłos, echo), budowę miksera GStreamer, kolejne iteracje wzmocnienia i limitera przy normalizacji, kontrolę szczytów
po kodowaniu MP3/MP4 i zapis plików. Przy starcie jest schowany – otwiera się dopiero po kliknięciu ikony terminala.

## Pozostałe

- Ekran startowy z wersją, interfejs **PL / EN** (automatycznie wg systemu, przełącznik w menu).
- Ikona w menu aplikacji i docku przełącza się **dark / light** razem z motywem systemu, także gdy aplikacja jest zamknięta.
- Zamknięcie okna kończy aplikację (w trakcie pracy z pytaniem o potwierdzenie). Powiadomienie po zakończeniu.
- Oryginalne pliki nigdy nie są zmieniane.

## Instalacja

Najnowszy plik `linux-project-mastering-audio_<wersja>_all.deb` pobierz ze [strony Releases](https://github.com/jgu-linux-apps/linux-project-mastering-audio/releases/latest):

```bash
sudo apt install ./linux-project-mastering-audio_<wersja>_all.deb
```

Wymagania: Ubuntu 24.04+ (libadwaita ≥ 1.5). Zależności instalują się same: GTK4/libadwaita, GStreamer,
numpy, scipy, python3-soundfile, ffmpeg, fdkaac (repozytorium *multiverse*, w standardowym Ubuntu włączone).

```bash
linux-project-mastering-audio --version
linux-project-mastering-audio --icon-sync      # jednorazowe przełączenie ikony
linux-project-mastering-audio pliki*.wav       # otwórz z plikami (trafiają do aktywnej zakładki)
```

## Budowanie ze źródeł

Kod źródłowy jest w katalogu `src/` repozytorium; paczek `.deb` nie ma w gicie, są w [Releases](https://github.com/jgu-linux-apps/linux-project-mastering-audio/releases).
Wypchnięcie tagu `vX.Y.Z` zgodnego z `VERSION` w `src/src/pma/__init__.py` uruchamia GitHub Actions
(`.github/workflows/release.yml`), które budują paczkę i publikują wydanie. Polecenia uruchamiaj w `src/`:

```bash
python3 tools/make_assets.py data          # ikony + ekran startowy
./packaging/build-deb.sh                    # -> dist/linux-project-mastering-audio_<wersja>_all.deb
./bin/linux-project-mastering-audio         # uruchomienie bez instalacji
```

Struktura: `src/pma/engine/vocal.py` (mastering wokalu, efekty, scalanie), `src/pma/engine/normalize.py`
(normalizacja albumu), `src/pma/engine/dsp.py` (LUFS BS.1770-4, true peak, kompresor, limiter),
`src/pma/engine/export.py` (WAV/MP3/MP4), `src/pma/ui/` (GTK4/libadwaita, mikser na żywo w GStreamer),
`tests/` (generatory testowych ścieżek).

## Historia wersji

- **0.2.4** – bez zmian w aplikacji: kod w repozytorium w katalogu `src/`, paczka `.deb` na stronie GitHub Releases (budowana automatycznie dla każdego tagu wersji); README: instalacja z Releases.
- **0.2.3** – mini-terminal schowany przy starcie, otwiera się dopiero po kliknięciu ikony.
- **0.2.2** – podpis „made by: JGu / Supported by Claude” na ekranie startowym i w „O programie”; poprawna odmiana liczebników (1 utwór, 4 utwory, 5 utworów; 1 track / 2 tracks) i przecinek dziesiętny w polskiej wersji.
- **0.2.1** – nazwa **Linux Project Mastering Audio** wszędzie (ekran startowy, okno, menu, raport); mini-terminal z podglądem pracy silnika; w raporcie albumu kolumna „Refren”.
- **0.2.0** – nowy podział: zakładka **Wokal** (5 opcji masteringu wokalu z pogłosem/echem, suwaki głośności
  i efektu, odsłuch na żywo z miernikiem, scalanie do jednego WAV) i zakładka **Album** (tylko normalizacja:
  4 poziomy docelowe, 3 sposoby wyrównania).
- **0.1.1** – usunięta ikona w trayu; zamknięcie w trakcie pracy pyta o potwierdzenie.
- **0.1.0** – pierwsza wersja.

---

# English

**Linux Project Mastering Audio** – two tabs:

- **Vocals:** drop 1–10 vocal WAVs (lead, ad-libs, backing…), pick one of 5 vocal mastering options
  (Studio, Radio, Warm, Space, Rap – EQ, de-esser, compression, saturation, air + reverb/echo), set a **volume**
  and **reverb/echo** slider per track while listening live (peak meter included), then **MERGE ALL TRACKS INTO ONE**
  → a single 24-bit WAV that sounds exactly like the live preview, clip-protected at −1 dBTP.
- **Album:** drop finished tracks and **NORMALIZE WHOLE ALBUM** – no change to the sound, just an even level:
  targets Streaming (−14), Apple Music (−16), CD/store (−10), Loud (−8 LUFS); methods equal choruses (recommended),
  equal average loudness, or one album gain. Export WAV / MP3 / MP4 with cover art and tags, plus a report.

PL/EN UI, a mini terminal (top-right) showing what the engine is doing live, splash with version, dark/light app icon that follows the system theme. Ubuntu 24.04+.

---

made by: JGu · Supported by Claude
