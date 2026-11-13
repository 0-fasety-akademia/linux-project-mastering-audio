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
   | **Pop** | jasny i do przodu, gęsta kompresja | pogłos + krótkie echo (22%) |
   | **Akustyczny** | naturalny, lekka kompresja | mała sala (18%) |
   | **R&B / Soul** | ciepły i gładki | długi pogłos + echo ping-pong (30%) |
   | **Mowa** | podcast, lektor – sucho i wyraźnie | bez efektu (0%) |
   | **Lo-fi** | wąskie pasmo, nasycenie, vintage | mały pogłos + echo (25%) |
   | **MANUAL** | wszystko ustawiasz sam suwakami | – |

   Po wyborze **MANUAL** pod ścieżkami pojawiają się kafle z suwakami (2–4 w rzędzie, zależnie od szerokości okna):
   **Barwa (EQ)** – filtr dołu, ciało 200 Hz, błoto 350 Hz, obecność 3,5 kHz, powietrze 12 kHz;
   **Kompresja** – próg, stopień, atak, powrót; **De-esser i nasycenie**; **Przestrzeń** – pogłos, jego opóźnienie,
   echo i powtórzenia echa. Zmiany słychać po ok. sekundzie od puszczenia suwaka; ustawienia są zapamiętywane.

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
2. **Płyta w liczbach** – wykres: głośność każdego utworu przed i po (LUFS), linia celu i zakres dynamiki (LRA).
   Przed normalizacją słupki „po” są przewidywane, po normalizacji – zmierzone.
3. **Mastering miksu** (opcjonalnie, przed normalizacją): **Bez masteringu**, **Delikatny**, **Ciepły**,
   **Nowoczesny**, **Mocny** – filtr subsoniczny, korekcja barwy, kompresja „sklejająca”, delikatne nasycenie.
   Głośność utworu po masteringu zostaje taka sama, więc wyrównanie płyty działa jak wcześniej.
4. **Poziom docelowy** (z pułapem szczytów dobranym do celu):
   - Streaming – Spotify, YouTube (−14 LUFS) – szczyty do −1 dBTP
   - Apple Music (−16 LUFS) – szczyty do −1 dBTP
   - CD / sklep (−10 LUFS) – szczyty do **−2 dBTP**
   - Głośno – klub, rap (−8 LUFS) – szczyty do **−2 dBTP**
   - **Własny (MANUAL)** – wpisujesz poziom od −30 do −5 LUFS (pod polem jest podpowiedź z typowymi wartościami);
     pułap −1 dBTP do −14 LUFS włącznie, głośniej −2 dBTP

   Głośne mastery po przekodowaniu w serwisach (Ogg, AAC, Opus) zyskują wyższe szczyty, dlatego dostają 1 dB więcej zapasu
   (tak zaleca Spotify dla materiału głośniejszego niż −14 LUFS).
5. **Sposób wyrównania:**
   - **Równe refreny (zalecane)** – głośne fragmenty wszystkich utworów na tym samym poziomie; spokojne zwrotki zachowują dynamikę,
   - **Równa średnia głośność** – identyczny LUFS każdego utworu,
   - **Jedno wzmocnienie dla płyty** – najgłośniejszy utwór trafia w cel, reszta dostaje to samo wzmocnienie (zachowuje różnice z miksu).
6. **Zapis:** WAV (CD 16 bit/44,1 kHz z ditherem albo Hi-Res 24 bit), MP3 320 kbps, MP4 (AAC 256 kbps, koder FDK) –
   z okładką PNG i tagami (tytuł z nazwy pliku, wykonawca, album, numer).
7. **NORMALIZUJ CAŁY ALBUM** → folder **`normalized/`** obok oryginałów + `raport.txt` (przed/po, refren, LRA
   i to, o ile dB limiter ściął szczyty). Jeśli w którymś utworze ściął więcej niż 3 dB, aplikacja ostrzega – master może brzmieć płasko.
8. **Odsłuch A/B** (po normalizacji): wybierasz utwór i przełączasz **A · oryginał** / **B · po** w trakcie odtwarzania.
   Obie wersje grają z **tą samą głośnością** (głośniejsza jest ściszana), więc słychać tylko różnicę brzmienia –
   bez złudzenia, że „głośniej = lepiej”. Pod odtwarzaczem dokładny pomiar wg EBU R128 dla A i B jednocześnie:
   głośność **chwilowa** (400 ms), **krótkookresowa** (3 s) i **zintegrowana**, odświeżana co 100 ms;
   kolumna słyszanej wersji jest podświetlona, a miernik pokazuje jej głośność chwilową.

Bez masteringu brzmienie się nie zmienia: tylko wzmocnienie + ochrona szczytów (miękki clipper i limiter true-peak).
MP3 i MP4 są sprawdzane **po zakodowaniu** i w razie przesteru automatycznie poprawiane.

## Motywy

Menu (☰) → **Motyw** – zmiana od razu, bez restartu, zapamiętywana:

- **Systemowy** – standardowy wygląd Ubuntu/GNOME (jasny lub ciemny jak system),
- **Neon Studio** – ciemne szkło i gradient cyjan → fiolet → róż z ikony aplikacji, świecące słupki i miernik,
- **Hologram** – wygląd ekranu z kokpitu: siatka, ostre krawędzie, cyfry o stałej szerokości, segmentowy miernik,
- **Konsola analogowa** – grafit i bursztyn, przyciski jak na sprzęcie studyjnym, wskazówkowy miernik VU w odsłuchu A/B.

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

- **0.4.0** – zakładka Wokal: 5 nowych opcji (Pop, Akustyczny, R&B / Soul, Mowa, Lo-fi) i **MANUAL** z kaflami suwaków
  (EQ, kompresja, de-esser i nasycenie, przestrzeń), szersza strona; Album: **własny poziom docelowy (MANUAL)**
  z podpowiedzią, **dokładny pomiar LUFS na żywo w A/B** (chwilowa / krótkookresowa / zintegrowana), krótkie nazwy
  na listach z opisem pod spodem (bez uciętych „…”), nazwy plików wokalu w dwóch liniach. Oraz wszystko poniżej
  (wersja 0.3.0 nie była publikowana): zakładka Album: **mastering miksu** (Delikatny, Ciepły, Nowoczesny, Mocny), **pułap szczytów zależny od celu**
  (−2 dBTP dla CD i „Głośno”), **wykres płyty** (LUFS przed/po, LRA), **odsłuch A/B z wyrównaną głośnością**,
  w raporcie LRA i ścięcie limitera z ostrzeżeniem powyżej 3 dB; typograficzny minus w liczbach (−2,0 dBTP);
  poprawiona statystyka kompresora w logu; link do strony projektu w „O programie” i w paczce;
  **motywy**: Systemowy, Neon Studio, Hologram, Konsola analogowa (menu → Motyw), miernik poziomu w odsłuchu A/B.
  Zakładka Album w **dwóch równych kolumnach** (utwory i wykres | ustawienia), odsłuch A/B pod spodem na całą szerokość;
  w wąskim oknie jedna kolumna. Przewijanie w odsłuchu (A/B i Wokal) bez zawieszania: skok dopiero po zatrzymaniu suwaka,
  a gdy odtwarzanie mimo to stanie, odtwarzacz sam się odbudowuje w tym samym miejscu.

- **0.2.5** – licencja: aplikacja jest teraz na licencji Freeware License (No Modifications), zob. `LICENSE` — darmowe użytkowanie i udostępnianie bez zmian, bez prawa do modyfikacji; poza tym bez zmian w aplikacji.
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

- **Vocals:** drop 1–10 vocal WAVs (lead, ad-libs, backing…), pick one of 10 vocal mastering options
  (Studio, Radio, Warm, Space, Rap, Pop, Acoustic, R&B / Soul, Speech, Lo-fi – EQ, de-esser, compression, saturation,
  air + reverb/echo) or **MANUAL** with slider tiles (EQ, compression, de-esser & saturation, space), set a **volume**
  and **reverb/echo** slider per track while listening live (peak meter included), then **MERGE ALL TRACKS INTO ONE**
  → a single 24-bit WAV that sounds exactly like the live preview, clip-protected at −1 dBTP.
- **Album:** drop finished tracks and **NORMALIZE WHOLE ALBUM** for an even level:
  targets Streaming (−14), Apple Music (−16), CD/store (−10), Loud (−8 LUFS), with a peak ceiling matched to the target
  (−1 dBTP for streaming/Apple, −2 dBTP for loud masters) or a **custom (MANUAL) LUFS value**; methods equal choruses (recommended),
  equal average loudness, or one album gain. Optional **mix mastering** (Gentle, Warm, Modern, Punchy),
  an **album chart** (LUFS before/after, LRA) and **loudness-matched A/B listening** of original vs result with
  live EBU R128 readings (momentary, short-term, integrated) for both versions.
  Export WAV / MP3 / MP4 with cover art and tags, plus a report with LRA and limiter warnings.

Themes (menu → Theme): System, Neon Studio, Hologram, Analog console – switched live, with a themed level meter in A/B.
PL/EN UI, a mini terminal (top-right) showing what the engine is doing live, splash with version, dark/light app icon that follows the system theme. Ubuntu 24.04+.

---

made by: JGu · Supported by Claude
