"""
Render a neofetch-style info card SVG that sits beside the ASCII portrait:
a title bar, a typed `neofetch` prompt, then colored key/value rows that
fade + slide in one after another, the classic neofetch colour strip, and a
blinking prompt cursor at the end. Hand-authored SVG with CSS keyframes and
SMIL only (GitHub runs both inside <img>, never JS). No data fetch -- edit
the ROWS list below to change the content, then re-run.

Canvas is 840 x 880, the same as the portrait, so the two line up side by
side at equal widths in the README table.

    python scripts/make_info_card.py [output.svg]
    STATIC=1 python scripts/make_info_card.py   -> frozen frame for previews
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

USER = "neva"
HOST = "github"

# (key, [value line, continuation line, ...]) -- keep each line <= 40 chars
ROWS = [
    ("Role",      ["Computer Engineer"]),
    ("Focus",     ["Computer Vision · NLP · Data Science"]),
    ("Languages", ["Python · TypeScript"]),
    ("Stack",     ["React · Vite · OpenCV · MediaPipe",
                   "NumPy · pandas · Streamlit"]),
    ("Now",       ["FootworkCoach — camera-based kickboxing",
                   "footwork trainer, runs fully on-device"]),
    ("Also",      ["Hand-Gesture-Music · TRNewsSummarizer"]),
    ("Speaks",    ["Türkçe · English · Español"]),
    ("GitHub",    ["since Jul 2024"]),
]

W, H = 840, 880                       # == portrait svg canvas
PAD = 20
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
KEY = "#22d3ee"                       # key colour (neofetch bold)
NAME = "#39d353"                      # user@host colour
STRIP = ["#ff5f56", "#ffbd2e", "#27c93f", "#22d3ee", "#1f6feb", "#bc8cff", "#f778ba", "#e6edf3"]

FONT = 23
PROMPT_FONT = 22
KEY_X = 40
VAL_X = 215
ROW_Y0 = 230
ROW_STEP = 46

# ---- timing (seconds, one-shot) -----------------------------------------
T_TYPE0, TYPE_DUR = 0.2, 0.8          # prompt types itself in
T_NAME = T_TYPE0 + TYPE_DUR + 0.15    # user@host + underline
T_ROWS0, ROW_STAGGER = T_NAME + 0.3, 0.13
n_lines = sum(len(v) for _, v in ROWS)
T_STRIP0, STRIP_STAGGER = T_ROWS0 + n_lines * ROW_STAGGER + 0.3, 0.03
T_PROMPT = T_STRIP0 + 2 * len(STRIP) * STRIP_STAGGER + 0.3
FADE_DUR = 0.45


def esc(s):
    return html.escape(s, quote=False)


def fade(delay):
    """class+style attrs for a fade/slide-in element (none in STATIC mode)."""
    return "" if STATIC else f' class="r" style="animation-delay:{delay:.2f}s"'


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>'
    f'.r{{opacity:0;animation:in {FADE_DUR}s ease-out both}}'
    '@keyframes in{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}'
    '@media (prefers-reduced-motion: reduce){.r{opacity:1!important;transform:none!important;animation:none!important}}'
    '</style>',
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
    '</defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">{USER}@{HOST}: ~$ neofetch</text>')

# ---- typed prompt: neva@github:~$ neofetch --------------------------------
prompt_y = 84
prompt_txt = (f'<text x="{KEY_X}" y="{prompt_y}" font-size="{PROMPT_FONT}" fill="{MUTED}">'
              f'{USER}@{HOST}:~$ <tspan fill="{INK}">neofetch</tspan></text>')
if STATIC:
    parts.append(prompt_txt)
else:
    typed_w = len(f"{USER}@{HOST}:~$ neofetch") * PROMPT_FONT * 0.62
    parts.append(f'<clipPath id="type"><rect x="{KEY_X}" y="{prompt_y - PROMPT_FONT}" height="{PROMPT_FONT * 1.4:.0f}" width="0">'
                 f'<animate attributeName="width" from="0" to="{typed_w:.0f}" begin="{T_TYPE0}s" dur="{TYPE_DUR}s" fill="freeze"/>'
                 f'</rect></clipPath>')
    parts.append(f'<g clip-path="url(#type)">{prompt_txt}</g>')

# ---- user@host + underline ---------------------------------------------
name_y = 142
parts.append(f'<text{fade(T_NAME)} x="{KEY_X}" y="{name_y}" font-size="30" font-weight="700" fill="{NAME}">'
             f'{USER}<tspan fill="{INK}" font-weight="400">@</tspan>{HOST}</text>')
parts.append(f'<text{fade(T_NAME + 0.1)} x="{KEY_X}" y="{name_y + 26}" font-size="{FONT}" fill="{MUTED}">'
             f'{"-" * (len(USER) + 1 + len(HOST))}</text>')

# ---- key / value rows ---------------------------------------------------
line_i = 0
for key, lines in ROWS:
    for j, val in enumerate(lines):
        y = ROW_Y0 + line_i * ROW_STEP
        delay = T_ROWS0 + line_i * ROW_STAGGER
        parts.append(f'<g{fade(delay)}>')
        if j == 0:
            parts.append(f'<text x="{KEY_X}" y="{y}" font-size="{FONT}" font-weight="700" fill="{KEY}">{esc(key)}</text>')
            parts.append(f'<text x="{VAL_X - 22}" y="{y}" font-size="{FONT}" fill="{MUTED}">:</text>')
        parts.append(f'<text x="{VAL_X}" y="{y}" font-size="{FONT}" fill="{INK}">{esc(val)}</text>')
        parts.append('</g>')
        line_i += 1

# ---- neofetch colour strip ---------------------------------------------
strip_y = ROW_Y0 + line_i * ROW_STEP + 14
blk_w, blk_h, blk_gap = 60, 28, 4
for row in range(2):
    for k, color in enumerate(STRIP):
        x = KEY_X + k * (blk_w + blk_gap)
        y = strip_y + row * (blk_h + blk_gap)
        delay = T_STRIP0 + (row * len(STRIP) + k) * STRIP_STAGGER
        op = "1" if row == 0 else "0.5"
        parts.append(f'<rect{fade(delay)} x="{x}" y="{y}" width="{blk_w}" height="{blk_h}" rx="4" '
                     f'fill="{color}" fill-opacity="{op}"/>')

# ---- final prompt with blinking cursor ---------------------------------
end_y = H - PAD - 36
parts.append(f'<text{fade(T_PROMPT)} x="{KEY_X}" y="{end_y}" font-size="{PROMPT_FONT}" fill="{MUTED}">{USER}@{HOST}:~$ </text>')
cursor_x = KEY_X + len(f"{USER}@{HOST}:~$ ") * PROMPT_FONT * 0.62
if STATIC:
    cursor_attr, cursor_anim = "", ""
else:
    cursor_attr = ' opacity="0"'
    cursor_anim = (f'<set attributeName="opacity" to="1" begin="{T_PROMPT:.2f}s"/>'
                   f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" '
                   f'begin="{T_PROMPT + 0.6:.2f}s" repeatCount="indefinite"/>')
parts.append(f'<rect x="{cursor_x:.0f}" y="{end_y - PROMPT_FONT + 2}" width="{PROMPT_FONT*0.6:.0f}" '
             f'height="{PROMPT_FONT}" fill="{INK}"{cursor_attr}>{cursor_anim}</rect>')

parts.append('</svg>')
svg = "".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB, {len(ROWS)} rows / {n_lines} lines, ends at {T_PROMPT:.1f}s")
