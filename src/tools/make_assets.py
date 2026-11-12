import math, random, os


THEMES = {
    "dark": dict(bg1="#1A2140", bg2="#06080F", stroke="#2A3358",
                 g1="#00E5FF", g2="#8B5CF6", g3="#FF3EA5", glow=5, dim="#3B4570"),
    "light": dict(bg1="#FFFFFF", bg2="#E3E8F4", stroke="#C9D1E6",
                  g1="#0072FF", g2="#6D28D9", g3="#E0157A", glow=2.5, dim="#B6C0DA"),
}


def defs(t, uid):
    return f"""
  <defs>
    <radialGradient id="bg{uid}" cx="50%" cy="35%" r="75%">
      <stop offset="0" stop-color="{t['bg1']}"/><stop offset="1" stop-color="{t['bg2']}"/>
    </radialGradient>
    <linearGradient id="neon{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['g1']}"/><stop offset=".55" stop-color="{t['g2']}"/>
      <stop offset="1" stop-color="{t['g3']}"/>
    </linearGradient>
    <linearGradient id="neonh{uid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['g1']}"/><stop offset=".55" stop-color="{t['g2']}"/>
      <stop offset="1" stop-color="{t['g3']}"/>
    </linearGradient>
    <filter id="glow{uid}" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="{t['glow']}" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>"""


def squircle(uid, t):
    return (f'<rect x="12" y="12" width="232" height="232" rx="58" fill="url(#bg{uid})" '
            f'stroke="{t["stroke"]}" stroke-width="2"/>')


def arc(cx, cy, r, a0, a1):
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{p0[0]:.1f},{p0[1]:.1f} A{r},{r} 0 {large} 1 {p1[0]:.1f},{p1[1]:.1f}"


# ---------- Koncepcja A: PULSAR ----------
def icon_pulsar(theme):
    t, u = THEMES[theme], "A" + theme
    pts = []
    for i in range(0, 121):
        x = 58 + i * (140 / 120)
        e = math.sin(math.pi * i / 120) ** 1.6
        y = 128 - 46 * e * math.sin(i / 120 * math.pi * 7)
        pts.append(f"{x:.1f},{y:.1f}")
    wave = " ".join(pts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">{defs(t, u)}
  {squircle(u, t)}
  <path d="{arc(128,128,86,135,405)}" fill="none" stroke="{t['dim']}" stroke-width="10" stroke-linecap="round" opacity=".55"/>
  <path d="{arc(128,128,86,135,350)}" fill="none" stroke="url(#neon{u})" stroke-width="10" stroke-linecap="round" stroke-dasharray="7 6" filter="url(#glow{u})"/>
  <circle cx="128" cy="128" r="66" fill="none" stroke="url(#neon{u})" stroke-width="2" opacity=".6"/>
  <polyline points="{wave}" fill="none" stroke="url(#neonh{u})" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow{u})"/>
  <circle cx="{128+86*math.cos(math.radians(350)):.1f}" cy="{128+86*math.sin(math.radians(350)):.1f}" r="7" fill="{t['g3']}" filter="url(#glow{u})"/>
</svg>"""


# ---------- Koncepcja B: PRISM ----------
def icon_prism(theme):
    t, u = THEMES[theme], "B" + theme
    hexp = " ".join(f"{128+92*math.cos(math.radians(a)):.1f},{128+92*math.sin(math.radians(a)):.1f}"
                    for a in range(-90, 270, 60))
    bars = []
    n = 9
    for i in range(n):
        x = 76 + i * 13
        h = 22 + 52 * math.exp(-((i - 3.2) ** 2) / 6) + 14 * math.sin(i * 1.7) ** 2
        h = min(h, 70)
        bars.append(f'<rect x="{x-4}" y="{170-h:.1f}" width="8" height="{h:.1f}" rx="4" fill="url(#neon{u})"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">{defs(t, u)}
  {squircle(u, t)}
  <polygon points="{hexp}" fill="none" stroke="url(#neon{u})" stroke-width="6" stroke-linejoin="round" filter="url(#glow{u})"/>
  <polygon points="{hexp}" fill="none" stroke="{t['g1']}" stroke-width="1.5" opacity=".35" transform="translate(128 128) scale(.84) translate(-128 -128)"/>
  <g filter="url(#glow{u})">{''.join(bars)}</g>
  <line x1="68" y1="96" x2="188" y2="96" stroke="{t['g3']}" stroke-width="3" stroke-dasharray="6 5" stroke-linecap="round" filter="url(#glow{u})"/>
</svg>"""


# ---------- Koncepcja C: TAMED WAVE ----------
def wave_bars(x0, x1, cy, step, wild, tame, seed=7, width=4):
    random.seed(seed)
    out = []
    n = int((x1 - x0) / step)
    for i in range(n + 1):
        x = x0 + i * step
        p = i / n
        mix = 1 / (1 + math.exp(-(p - 0.5) * 12))   # przejscie chaos -> kontrola
        raw = wild * (0.35 + 0.65 * random.random()) * (0.6 + 0.4 * math.sin(i * 0.9) ** 2)
        tm = tame * (0.86 + 0.14 * random.random())
        h = raw * (1 - mix) + tm * mix
        out.append((x, cy - h, 2 * h))
    return out


def icon_tamed(theme):
    t, u = THEMES[theme], "C" + theme
    bars = "".join(f'<rect x="{x-2.5:.1f}" y="{y:.1f}" width="5" height="{h:.1f}" rx="2.5" fill="url(#neonh{u})"/>'
                   for x, y, h in wave_bars(54, 202, 128, 8.2, 62, 30))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">{defs(t, u)}
  {squircle(u, t)}
  <circle cx="128" cy="128" r="94" fill="none" stroke="url(#neon{u})" stroke-width="3" opacity=".85" filter="url(#glow{u})"/>
  <g filter="url(#glow{u})">{bars}</g>
  <line x1="128" y1="94" x2="206" y2="94" stroke="{t['g3']}" stroke-width="2.5" stroke-linecap="round" filter="url(#glow{u})"/>
  <line x1="128" y1="162" x2="206" y2="162" stroke="{t['g3']}" stroke-width="2.5" stroke-linecap="round" filter="url(#glow{u})"/>
</svg>"""


# ---------- Symboliczne ikony do traya (GNOME przebarwia #2e3436) ----------
SYM = {
    "A": """<path d="M3.3 12.2 A6 6 0 1 1 12.7 12.2" fill="none" stroke="#2e3436" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="1.6 1.2"/>
  <path d="M4 8 Q5 4.6 6 8 T8 8 T10 8 T12 8" fill="none" stroke="#2e3436" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>""",
    "B": """<polygon points="8,1 14.1,4.5 14.1,11.5 8,15 1.9,11.5 1.9,4.5" fill="none" stroke="#2e3436" stroke-width="1.4" stroke-linejoin="round"/>
  <rect x="4.6" y="7" width="1.5" height="4.5" rx=".75" fill="#2e3436"/><rect x="7.25" y="5.6" width="1.5" height="5.9" rx=".75" fill="#2e3436"/><rect x="9.9" y="8" width="1.5" height="3.5" rx=".75" fill="#2e3436"/>""",
    "C": """<circle cx="8" cy="8" r="6.8" fill="none" stroke="#2e3436" stroke-width="1.3"/>
  <rect x="3.6" y="3.8" width="1.4" height="8.4" rx=".7" fill="#2e3436"/><rect x="5.8" y="5" width="1.4" height="6" rx=".7" fill="#2e3436"/>
  <rect x="8" y="6.3" width="1.4" height="3.4" rx=".7" fill="#2e3436"/><rect x="10.2" y="6.3" width="1.4" height="3.4" rx=".7" fill="#2e3436"/>""",
}


def sym(k):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">{SYM[k]}</svg>'


# ---------- Ekrany startowe 640x400 ----------
def splash_common(u, t):
    grid = []
    for i in range(-12, 13):
        grid.append(f'<line x1="{320+i*16}" y1="300" x2="{320+i*90}" y2="400"/>')
    for j, y in enumerate([304, 312, 324, 340, 362, 392]):
        grid.append(f'<line x1="0" y1="{y}" x2="640" y2="{y}"/>')
    return f"""{defs(t, u)}
  <defs>
    <linearGradient id="fade{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient>
    <mask id="gm{u}"><rect x="0" y="300" width="640" height="100" fill="url(#fade{u})"/></mask>
    <radialGradient id="sbg{u}" cx="50%" cy="40%" r="80%"><stop offset="0" stop-color="#151B36"/><stop offset="1" stop-color="#04050B"/></radialGradient>
  </defs>
  <rect width="640" height="400" rx="18" fill="url(#sbg{u})"/>
  <g stroke="{t['g2']}" stroke-width="1" opacity=".55" mask="url(#gm{u})">{''.join(grid)}</g>
  <line x1="0" y1="300" x2="640" y2="300" stroke="url(#neonh{u})" stroke-width="1.5" opacity=".8"/>"""


def splash_footer(u, t, version="v1.0.0"):
    return f"""
  <text x="40" y="350" font-family="Inter" font-size="11.5" fill="#8C96BE" letter-spacing=".5">Ładowanie silnika audio…</text>
  <rect x="40" y="360" width="560" height="4" rx="2" fill="#1E2547"/>
  <rect x="40" y="360" width="330" height="4" rx="2" fill="url(#neonh{u})" filter="url(#glow{u})"/>
  <text x="600" y="350" text-anchor="end" font-family="Inter" font-size="11.5" fill="#8C96BE">{version}</text>"""


def splash1(footer=True):
    t, u = THEMES["dark"], "S1"
    pts = []
    for i in range(0, 401):
        x = i * 1.6
        e = 0.25 + 0.75 * math.exp(-((i - 270) / 90) ** 2)
        y = 205 - 42 * e * math.sin(i * 0.19) * math.cos(i * 0.031)
        pts.append(f"{x:.1f},{y:.1f}")
    icon = icon_pulsar("dark").split(">", 1)[1].rsplit("</svg>", 1)[0]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" width="640" height="400">{splash_common(u, t)}
  <polyline points="{' '.join(pts)}" fill="none" stroke="url(#neonh{u})" stroke-width="2.5" opacity=".9" filter="url(#glow{u})"/>
  <path d="{arc(500,250,120,200,330)}" fill="none" stroke="{t['g2']}" stroke-width="1.5" opacity=".35"/>
  <path d="{arc(500,250,150,205,325)}" fill="none" stroke="{t['g1']}" stroke-width="1" opacity=".25" stroke-dasharray="4 6"/>
  <svg x="40" y="44" width="92" height="92" viewBox="0 0 256 256">{icon}</svg>
  <text x="148" y="82" font-family="Inter Display" font-weight="300" font-size="15" letter-spacing="7" fill="#9AA6D6">LINUX PROJECT</text>
  <text x="146" y="122" font-family="Inter Display" font-weight="700" font-size="38" letter-spacing="3" fill="#F2F5FF">MASTERING AUDIO</text>
  <text x="148" y="144" font-family="Inter" font-size="11" letter-spacing="3" fill="url(#neonh{u})">LOUDNESS · DYNAMICS · CLARITY</text>
  {splash_footer(u, t) if footer else ''}
</svg>"""


def splash2():
    t, u = THEMES["dark"], "S2"
    bars = "".join(
        f'<rect x="{x-2.2:.1f}" y="{y:.1f}" width="4.4" height="{h:.1f}" rx="2.2" fill="url(#neonh{u})"/>'
        for x, y, h in wave_bars(30, 610, 220, 8, 50, 26, seed=3))
    icon = icon_tamed("dark").split(">", 1)[1].rsplit("</svg>", 1)[0]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" width="640" height="400">{splash_common(u, t)}
  <g opacity=".55" filter="url(#glow{u})">{bars}</g>
  <line x1="320" y1="190" x2="612" y2="190" stroke="{t['g3']}" stroke-width="1.5" opacity=".9" filter="url(#glow{u})"/>
  <line x1="320" y1="250" x2="612" y2="250" stroke="{t['g3']}" stroke-width="1.5" opacity=".9" filter="url(#glow{u})"/>
  <text x="604" y="184" text-anchor="end" font-family="Inter" font-size="9.5" letter-spacing="2" fill="{t['g3']}">−1.0 dBTP</text>
  <svg x="274" y="30" width="92" height="92" viewBox="0 0 256 256">{icon}</svg>
  <text x="320" y="152" text-anchor="middle" font-family="Inter Display" font-weight="700" font-size="34" letter-spacing="4" fill="#F2F5FF">MASTERING AUDIO</text>
  <text x="320" y="292" text-anchor="middle" font-family="Inter Display" font-weight="300" font-size="13" letter-spacing="9" fill="#9AA6D6">PROJECT · FOR UBUNTU</text>
  {splash_footer(u, t)}
</svg>"""



if __name__ == "__main__":
    import subprocess
    import sys
    APP_ID = "io.github.jaro.LinuxProjectMasteringAudio"
    data = sys.argv[1]
    ic = os.path.join(data, "icons")
    for d in ("", "hicolor/scalable/apps", "hicolor/symbolic/apps"):
        os.makedirs(os.path.join(ic, d), exist_ok=True)
    w = lambda p, c: open(os.path.join(ic, p), "w").write(c)  # noqa: E731
    w("app-dark.svg", icon_pulsar("dark"))
    w("app-light.svg", icon_pulsar("light"))
    w(f"hicolor/scalable/apps/{APP_ID}.svg", icon_pulsar("dark"))
    w(f"hicolor/symbolic/apps/{APP_ID}-symbolic.svg", sym("A"))
    svg = splash1(footer=False)
    open(os.path.join(data, "splash.svg"), "w").write(svg)
    subprocess.run(["rsvg-convert", "-w", "1800", "-h", "1125", os.path.join(data, "splash.svg"),
                    "-o", os.path.join(data, "splash.png")], check=True)
    os.remove(os.path.join(data, "splash.svg"))
    print("assets ok")
