#!/bin/bash
# Buduje pakiet .deb: dist/linux-project-mastering-audio_<wersja>_all.deb
set -euo pipefail
cd "$(dirname "$0")/.."
PKG=linux-project-mastering-audio
APP_ID=io.github.jaro.LinuxProjectMasteringAudio
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' src/pma/__init__.py)
ROOT=$(mktemp -d)
trap 'rm -rf "$ROOT"' EXIT

install -d "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/usr/share/$PKG" "$ROOT/usr/share/applications" \
  "$ROOT/usr/share/icons/hicolor/scalable/apps" "$ROOT/usr/share/icons/hicolor/symbolic/apps" \
  "$ROOT/etc/xdg/autostart" "$ROOT/usr/share/doc/$PKG"

cp -r src data "$ROOT/usr/share/$PKG/"
find "$ROOT/usr/share/$PKG" -name __pycache__ -prune -exec rm -rf {} +
rm -rf "$ROOT/usr/share/$PKG/data/applications" "$ROOT/usr/share/$PKG/data/autostart"
install -m 755 bin/$PKG "$ROOT/usr/bin/$PKG"
install -m 644 data/applications/$APP_ID.desktop "$ROOT/usr/share/applications/"
install -m 644 data/autostart/$PKG-iconsync.desktop "$ROOT/etc/xdg/autostart/"
install -m 644 data/icons/app-dark.svg "$ROOT/usr/share/icons/hicolor/scalable/apps/$APP_ID.svg"
install -m 644 data/icons/hicolor/symbolic/apps/$APP_ID-symbolic.svg "$ROOT/usr/share/icons/hicolor/symbolic/apps/"
install -m 644 README.md "$ROOT/usr/share/doc/$PKG/"
install -m 644 LICENSE "$ROOT/usr/share/doc/$PKG/copyright"

SIZE=$(du -sk "$ROOT/usr" "$ROOT/etc" | awk '{s+=$1} END {print s}')
cat > "$ROOT/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: sound
Priority: optional
Architecture: all
Installed-Size: $SIZE
Maintainer: Jaro <jaroslawguza83@gmail.com>
Homepage: https://github.com/jgu-linux-apps/linux-project-mastering-audio
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1 (>= 1.5),
 python3-numpy, python3-scipy, python3-soundfile,
 gir1.2-gstreamer-1.0, gir1.2-gst-plugins-base-1.0, gstreamer1.0-plugins-good,
 ffmpeg, fdkaac, librsvg2-common
Description: Linux Project Mastering Audio – vocal mastering and album loudness normalization
 Vocals tab: master 1-10 vocal tracks with 5 styles (reverb/echo included),
 set volume and effect per track while listening live, merge into one WAV.
 Album tab: normalize the loudness of finished tracks to an even level
 (WAV / MP3 / MP4 with cover art), optional mix mastering,
 album chart and loudness-matched A/B listening. PL / EN.
EOF

cat > "$ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -f /usr/share/icons/hicolor || true
  command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
cat > "$ROOT/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -f /usr/share/icons/hicolor || true
command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
exit 0
EOF
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"
echo "/etc/xdg/autostart/$PKG-iconsync.desktop" > "$ROOT/DEBIAN/conffiles"

mkdir -p dist
dpkg-deb --root-owner-group --build "$ROOT" "dist/${PKG}_${VERSION}_all.deb" >/dev/null
echo "dist/${PKG}_${VERSION}_all.deb"
