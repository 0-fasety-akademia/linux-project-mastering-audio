# linux-project-mastering-audio — Linux Project Mastering Audio

A focused mastering app for Ubuntu with two tabs:

1. **Vocals** – master your vocal tracks (lead, ad-libs, backing vocals…), listen live with per-track volume and
   reverb/echo sliders, then **MERGE ALL TRACKS INTO ONE** → a single final WAV.
2. **Album** – finished, mixed songs: optional light **mix mastering**, **loudness normalization of the whole album**,
   an album chart and fair **A/B listening**, then **NORMALIZE**.

It is not another Audacity – just what you need. The interface is available in **English and Polish**.

---

## Vocals tab

1. Drop **1–10 WAV files** (mono or stereo; FLAC/AIFF work too). Tracks get the letters **A, B, C…** by file name.
   They should all start at the same moment (the way a DAW exports stems).
2. Pick a **mastering option** – the tile sets every track, and each track can be changed on its own:

   | Option | Character | Reverb / echo (start) |
   |---|---|---|
   | **Studio** | clean and clear | subtle plate reverb (15%) |
   | **Radio** | upfront, bright, firmer compression | short slap echo + small reverb (20%) |
   | **Warm** | soft and full, light saturation | velvet, longer reverb (28%) |
   | **Space** | lots of air | big reverb + ping-pong echo (40%) |
   | **Rap** | hard, crisp, close | dry, very short echo (12%) |
   | **Pop** | bright and upfront, dense compression | reverb + short echo (22%) |
   | **Acoustic** | natural, light compression | small room (18%) |
   | **R&B / Soul** | warm and smooth | long reverb + ping-pong echo (30%) |
   | **Speech** | podcast, voice-over – dry and clear | no effect (0%) |
   | **Lo-fi** | narrow band, saturation, vintage | small reverb + echo (25%) |
   | **AUTO-TUNE** | hard pitch correction – the robotic vocal effect | reverb + ping-pong echo (22%) |
   | **MANUAL** | you set everything with sliders | – |

   Every option is a chain of: low-cut filter, mud/presence correction, a two-pass **de-esser** (tames s / sh / ch),
   compression, saturation and air on top; the effect (reverb/echo) is sent after filtering, as in a pro mix.
   **AUTO-TUNE** detects the pitch every 10 ms and snaps it hard to the nearest semitone (A = 440 Hz) using its own
   TD-PSOLA engine – no extra libraries.

   With **MANUAL**, slider tiles appear under the tracks (2–4 per row depending on window width):
   **Tone (EQ)** – low cut, body 200 Hz, mud 350 Hz, presence 3.5 kHz, air 12 kHz; **Compression** – threshold, ratio,
   attack, release; **De-esser & saturation**; **Space** – reverb, pre-delay, echo and echo repeats. Changes are heard
   about a second after you release a slider, and the settings are remembered.
3. For every track: **Volume** (−24…+12 dB), **Reverb / echo** (0–100%; 0 = off), **Mute** (muted tracks are left out).
4. **Live listening** (bar at the bottom): sliders work during playback, the meter shows the peak of the sum and warns
   when it is too loud. Seeking is safe: the jump happens when the slider stops, and if playback ever stalls the
   player rebuilds itself at the same position.
5. **MERGE ALL TRACKS INTO ONE** – choose a file name and get **one 24-bit WAV** (sample rate of the first track) that
   sounds exactly like the live preview. If the sum goes above −1 dBTP, a true-peak limiter protects the peaks.

Processed tracks are cached in `~/.cache/linux-project-mastering-audio/vocal/`, so going back to an option you have
already heard is instant (the cache is safe to delete).

## Album tab

Two equal columns – tracks and the chart on the left, settings on the right – with A/B listening below at full width
(a single column in a narrow window).

1. Drop finished tracks (order = file names). Each one shows its loudness (LUFS), true peak (dBTP) and the
   **predicted change** for the chosen settings.
2. **The album in numbers** – a chart of every track's loudness before and after (LUFS), the target line and the
   loudness range (LRA). Before normalizing, the "after" bars are predicted; afterwards they are measured.
3. **Mix mastering** (optional, before normalization): **No mastering**, **Gentle**, **Warm**, **Modern**, **Punchy** –
   subsonic filter, tone correction, glue compression and gentle saturation. The track's loudness stays the same,
   so album levelling works exactly as before. **Listen to preview** plays 20 s of the loudest part of the chosen
   track with that mastering and level straight in the A/B player – before you normalize the whole album.
4. **Target level** (with a peak ceiling matched to the target):
   - Streaming – Spotify, YouTube (−14 LUFS) – peaks up to −1 dBTP
   - Apple Music (−16 LUFS) – peaks up to −1 dBTP
   - CD / store (−10 LUFS) – peaks up to **−2 dBTP**
   - Loud – club, rap (−8 LUFS) – peaks up to **−2 dBTP**
   - **Custom (MANUAL)** – type any level from −30 to −5 LUFS (a hint with typical values is shown below the field);
     ceiling −1 dBTP up to −14 LUFS, louder −2 dBTP

   Loud masters gain higher peaks when streaming services re-encode them (Ogg, AAC, Opus), so they get 1 dB more
   headroom – as Spotify recommends for material louder than −14 LUFS.
5. **Matching method:**
   - **Equal choruses (recommended)** – the loud parts of all songs at the same level; quiet verses keep their dynamics,
   - **Equal average** – identical LUFS for every song,
   - **One album gain** – the loudest song hits the target and the rest get the same gain (mix differences stay).
6. **Output:** WAV (CD 16 bit / 44.1 kHz with dither, or Hi-Res 24 bit), MP3 320 kbps, MP4 (AAC 256 kbps, FDK
   encoder) – with PNG cover art and tags (title from the file name, artist, album, track number).
7. **NORMALIZE** → a **`normalized/`** folder next to the originals + a report (before/after, chorus level, LRA and how
   many dB the limiter cut). If the limiter cut more than 3 dB on a track, the app warns you – the master may sound flat.
8. **A/B listening** (after normalizing or with a preview): pick a track and switch **A · original** / **B · after**
   while it plays. Both versions play at **the same loudness** (the louder one is turned down), so you hear only the
   difference in sound – no "louder = better" illusion. Below the player: precise **EBU R128** readings for A and B
   at once – **momentary** (400 ms), **short-term** (3 s) and **integrated** – refreshed every 100 ms, plus **two meters
   side by side** in the style of the current theme (the heard version is highlighted). Changing the mastering,
   target, method or track list stops an outdated A/B with a hint; going back to the last settings restores it.

Without mix mastering the sound does not change: only gain + peak protection (soft clipper and true-peak limiter).
MP3 and MP4 files are checked **after encoding** and corrected automatically if the codec pushed the peaks too high.

## Themes

Menu (☰) → **Theme** – switches live, no restart, and is remembered:

- **System** – the standard Ubuntu/GNOME look (light or dark like the system),
- **Neon Studio** – dark glass and the cyan → violet → pink gradient of the app icon, glowing bars and meters,
- **Hologram** – a cockpit HUD: grid, sharp edges, fixed-width digits, segmented meters,
- **Analog console** – graphite and amber, hardware-style buttons, needle VU meters in A/B,
- **Studio Pro (ergonomic)** – made for long sessions: no pure black or white, panels separated by slightly lighter
  backgrounds instead of bright frames, a single muted amber accent, tabular digits that don't jitter, translucent
  chart bars with a thin outline, and calm meter zones (green – safe, amber – caution, red only at the very top).

## Mini terminal

The terminal button in the title bar (top right) opens a small window that shows live what the engine is doing:
loading and measurements (LUFS, true peak), every vocal processing step (filter, EQ, de-esser, compression, reverb,
echo), the GStreamer mixer, gain and limiter iterations during normalization, peak checks after MP3/MP4 encoding and
file writes. It is hidden at start-up and opens only when you click the icon.

## Other

- Splash screen with the version; **English / Polish** interface (follows the system, switch in the menu).
- The icon in the app menu and dock follows the system **dark / light** theme, even while the app is closed.
- Closing the window quits the app (asks first while work is in progress). A notification when work is done.
- Original files are never changed.

## Installation

Download the latest `linux-project-mastering-audio_<version>_all.deb` from the
[Releases page](https://github.com/jgu-linux-apps/linux-project-mastering-audio/releases/latest):

```bash
sudo apt install ./linux-project-mastering-audio_<version>_all.deb
```

Requirements: Ubuntu 24.04+ (libadwaita ≥ 1.5). Dependencies install automatically: GTK4/libadwaita, GStreamer,
numpy, scipy, python3-soundfile, ffmpeg, fdkaac (from the *multiverse* repository, enabled on standard Ubuntu).

```bash
linux-project-mastering-audio --version
linux-project-mastering-audio --icon-sync      # switch the icon once
linux-project-mastering-audio files*.wav       # open with files (they go to the active tab)
```

## Building from source

The source code lives in the repository's `src/` folder; `.deb` packages are not in git, they are on
[Releases](https://github.com/jgu-linux-apps/linux-project-mastering-audio/releases). Pushing a `vX.Y.Z` tag that matches
`VERSION` in `src/src/pma/__init__.py` runs GitHub Actions (`.github/workflows/release.yml`), which build the package
and publish the release. Run the commands inside `src/`:

```bash
python3 tools/make_assets.py data          # icons + splash screen
./packaging/build-deb.sh                    # -> dist/linux-project-mastering-audio_<version>_all.deb
./bin/linux-project-mastering-audio         # run without installing
```

Layout: `src/pma/engine/vocal.py` (vocal mastering, effects, auto-tune, merging), `src/pma/engine/master.py`
(mix mastering), `src/pma/engine/normalize.py` (album normalization), `src/pma/engine/dsp.py` (BS.1770-4 LUFS,
true peak, compressor, limiter), `src/pma/engine/export.py` (WAV/MP3/MP4), `src/pma/ui/` (GTK4/libadwaita, themes,
live GStreamer mixer and A/B player), `tests/` (test track generators).

## Version history

- **0.5.1** – Vocals: new **AUTO-TUNE** option – hard pitch correction to the nearest semitone (own TD-PSOLA engine,
  no extra libraries); the **MANUAL** tile moved to the end. New **Studio Pro (ergonomic)** theme. README in English only.
- **0.5.0** – Album: **mastering preview** – 20 s of the loudest part of a chosen track with the selected mastering and
  level, straight in A/B; **two meters side by side** (A and B, themed, heard version highlighted); changing the
  settings **stops an outdated A/B** with a hint (going back restores it); the button now reads **NORMALIZE**.
- **0.4.0** – Vocals: 5 new options (Pop, Acoustic, R&B / Soul, Speech, Lo-fi) and **MANUAL** with slider tiles,
  wider page; Album: **custom target level (MANUAL)** with a hint, **live LUFS readings in A/B** (momentary /
  short-term / integrated), short list labels with a description underneath (no truncated text), vocal file names on
  two lines. Also everything developed as 0.3.0 (never published on its own): **mix mastering** (Gentle, Warm,
  Modern, Punchy), **target-based peak ceiling** (−2 dBTP for CD and Loud), **album chart** (LUFS before/after, LRA),
  **loudness-matched A/B listening**, LRA and limiter cut in the report with a warning above 3 dB, the **Neon Studio,
  Hologram and Analog console themes**, the Album tab in **two equal columns**, robust seeking (debounced, with a
  stall watchdog), typographic minus in numbers, project link in About and in the package.
- **0.2.5** – licence: the app is now under the Freeware License (No Modifications), see `LICENSE` – free to use and
  share unchanged, no right to modify; no other changes.
- **0.2.4** – no app changes: source code in the repository's `src/` folder, the `.deb` on GitHub Releases (built
  automatically for every version tag); README: installing from Releases.
- **0.2.3** – mini terminal hidden at start-up, opens only after clicking its icon.
- **0.2.2** – "made by: JGu / Supported by Claude" on the splash screen and in About; correct plural forms
  (1 track / 2 tracks, and the Polish forms) and a decimal comma in the Polish version.
- **0.2.1** – the name **Linux Project Mastering Audio** everywhere (splash, window, menu, report); mini terminal showing
  the engine at work; a "Chorus" column in the album report.
- **0.2.0** – new layout: a **Vocals** tab (5 vocal mastering options with reverb/echo, volume and effect sliders, live
  listening with a meter, merge into one WAV) and an **Album** tab (normalization only: 4 targets, 3 matching methods).
- **0.1.1** – tray icon removed; closing during work asks for confirmation.
- **0.1.0** – first version.

---

made by: JGu · Supported by Claude
