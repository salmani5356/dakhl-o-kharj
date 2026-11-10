#!/usr/bin/env python3
"""ساخت لوگوی «دخل و خرج»: SVG (متن به‌صورت مسیر، مستقل از فونت) + PNG. اجرا: python3 tools/make_brand.py"""
import io, math, sys
from pathlib import Path
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "brand"; OUT.mkdir(exist_ok=True)
FONTS = ROOT / "tools/fonts"

def load(name):
    f = TTFont(FONTS / name); f.flavor = None
    b = io.BytesIO(); f.save(b); data = b.getvalue()
    return TTFont(io.BytesIO(data)), hb.Font(hb.Face(data))
FA = {w: load(f"vazirmatn-arabic-{w}-normal.woff2") for w in (400, 500, 700, 900)}
FA["lal"] = load("lalezar-arabic-400-normal.woff2")
EN = {w: load(f"poppins-latin-{w}-normal.woff2") for w in (300, 500, 800, 900)}

def text_path(tt, hbf, text, size, rtl=False, tracking=0):
    """برمی‌گرداند (d, width) با مبدأ بالا-چپ باکس، خط پایهٔ متن در y=0 (بالا منفی)."""
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    if rtl: buf.direction = "rtl"; buf.script = "Arab"; buf.language = "fa"
    hb.shape(hbf, buf, {"kern": True, "liga": True})
    upem = tt["head"].unitsPerEm; k = size / upem
    gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    x = 0; d = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
        tp = TransformPen(pen, (k, 0, 0, -k, x + pos.x_offset * k, -pos.y_offset * k))
        gs[order[info.codepoint]].draw(tp)
        d.append(pen.getCommands()); x += pos.x_advance * k + tracking
    return " ".join(d), x

TQ1, TQ2, PU1, PU2, GR = "#bcd884", "#5a8530", "#f9b27a", "#d9553d", "#f6c445"
W_IN, W_MID, W_OUT = "#4d7a29", "#e0a11b", "#d4503a"
INK, CREAM = "#4a3042", "#fff8e1"

def defs(uid):
    return (f'<linearGradient id="t{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{TQ1}"/><stop offset="1" stop-color="{TQ2}"/></linearGradient>'
            f'<linearGradient id="p{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PU1}"/><stop offset="1" stop-color="{PU2}"/></linearGradient>')

def mark_inner(uid, mode="color", tilt=0):
    """نماد: دو سکهٔ هم‌پوشان. فیروزه‌ای = دخل، بنفش = خرج، و ناحیهٔ مشترکِ سبز = «تراز» (مانده)."""
    if mode == "color": fa, fb, fl, dot = f"url(#t{uid})", f"url(#p{uid})", GR, CREAM
    elif mode == "ink": fa, fb, fl, dot = INK, INK, INK, CREAM
    else: fa, fb, fl, dot = "#fff", "#fff", "#fff", INK
    opb = ' fill-opacity=".5"' if mode != "color" else ""
    lens_op = "" if mode == "color" else ' fill-opacity=".0"'
    cut = f'<clipPath id="c{uid}"><circle cx="128" cy="100" r="58"/></clipPath>'
    stitch = lambda cx: f'<circle cx="{cx}" cy="100" r="49" fill="none" stroke="{dot}" stroke-opacity=".5" stroke-width="2" stroke-dasharray="1.5 7.5" stroke-linecap="round"/>'
    lens = (f'<g clip-path="url(#c{uid})"><circle cx="72" cy="100" r="58" fill="{fl}"/></g>' if mode == "color" else
            f'<g clip-path="url(#c{uid})"><circle cx="72" cy="100" r="58" fill="{dot}"/></g>')
    return (f'<defs>{cut}</defs><circle cx="128" cy="100" r="58" fill="{fa}"/><circle cx="72" cy="100" r="58" fill="{fb}"{opb}/>'
            f'{stitch(128) if mode=="color" else ""}{stitch(72) if mode=="color" else ""}{lens}'
            f'<path d="M150 64A46 46 0 0 1 172 84" fill="none" stroke="#fff" stroke-opacity="{.6 if mode=="color" else 0}" stroke-width="5" stroke-linecap="round"/>'
            f'<path d="M28 84A46 46 0 0 1 50 64" fill="none" stroke="#fff" stroke-opacity="{.45 if mode=="color" else 0}" stroke-width="5" stroke-linecap="round"/>')

def svg(w, h, body, uid="a", bg=None, dfs=True):
    b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><defs>{defs(uid) if dfs else ""}</defs>{b}{body}</svg>'

def colors(mode):
    if mode == "color": return W_IN, W_MID, W_OUT, INK
    if mode == "ink": return INK, INK, INK, INK
    return "#fff", "#fff", "#fff", "#fff"

FA_W = (900, 400, 700); EN_W = (900, 300, 500)
def fa_word(size, mode="color", x0=0, y0=0, wts=None):
    """«دخل و خرج»: از راست: دخل، و، خرج؛ وزن‌ها متفاوت تا تباین کم/زیاد داشته باشد."""
    wts = wts or FA_W; a, b, c, _ = colors(mode)
    F = lambda w: FA[w]
    d1, w1 = text_path(*F(wts[0]), "دخل", size, rtl=True)
    d2, w2 = text_path(*F(wts[1]), "و", size * .78, rtl=True)
    d3, w3 = text_path(*F(wts[2]), "خرج", size, rtl=True)
    gap = size * .2; W = w1 + w2 + w3 + 2 * gap
    x1 = x0 + W - w1; x2 = x1 - gap - w2; x3 = x2 - gap - w3
    body = (f'<path transform="translate({x1:.1f} {y0})" d="{d1}" fill="{a}"/>'
            f'<path transform="translate({x2:.1f} {y0})" d="{d2}" fill="{b}"/>'
            f'<path transform="translate({x3:.1f} {y0})" d="{d3}" fill="{c}"/>')
    return body, W

def en_word(size, mode="color", x0=0, y0=0, sub=True, wts=None):
    wts = wts or EN_W; a, b, c, ink = colors(mode)
    d1, w1 = text_path(*EN[wts[0]], "Dakhl", size, tracking=-size * .02)
    d2, w2 = text_path(*EN[wts[1]], "o", size * .8)
    d3, w3 = text_path(*EN[wts[2]], "Kharj", size, tracking=-size * .01)
    gap = size * .16; W = w1 + w2 + w3 + 2 * gap
    body = (f'<path transform="translate({x0:.1f} {y0})" d="{d1}" fill="{a}"/>'
            f'<path transform="translate({x0+w1+gap:.1f} {y0})" d="{d2}" fill="{b}"/>'
            f'<path transform="translate({x0+w1+w2+2*gap:.1f} {y0})" d="{d3}" fill="{c}"/>')
    if sub:
        ds, ws = text_path(*EN[500], "INCOME · EXPENSE", size * .24, tracking=size * .11)
        body += f'<path transform="translate({x0+(W-ws)/2:.1f} {y0+size*.42:.1f})" d="{ds}" fill="{ink}" fill-opacity=".75"/>'
    return body, W

files = {}
for mode in ("color", "ink", "white"):
    sfx = "" if mode == "color" else f"-{mode}"
    bg = {"white": INK}.get(mode)
    # ۱) نماد تنها
    files[f"mark{sfx}.svg"] = svg(200, 200, mark_inner("m", mode), "m", bg=bg)
    # ۲) نوشتار فارسی / انگلیسی
    s = 120; b, W = fa_word(s, mode, 40, 40 + s * .78); files[f"wordmark-fa{sfx}.svg"] = svg(int(W + 80), int(s * 1.35 + 40), b, "a", bg=bg)
    s = 110; b, W = en_word(s, mode, 40, 40 + s * .74); files[f"wordmark-en{sfx}.svg"] = svg(int(W + 80), int(s * 1.1 + 60), b, "a", bg=bg)
    # ۳) ترکیبی افقی: نماد + نوشتار فارسی بالا + انگلیسی پایین
    fb, fw = fa_word(100, mode, 0, 0); eb, ew = en_word(54, mode, 0, 0, sub=False)
    gapx = 36; W = 200 + gapx + max(fw, ew) + 60
    body = f'<g transform="translate(30 25)">{mark_inner("h", mode)}</g>'
    body += f'<g transform="translate({230+gapx-30} 100)">{fb}</g>'
    body += f'<g transform="translate({230+gapx-30+(fw-ew)/2:.1f} 205)">{eb}</g>'
    files[f"lockup-horizontal{sfx}.svg"] = svg(int(230 + gapx - 30 + fw + 50), 250, body, "h", bg=bg)
    # ۴) ترکیبی عمودی
    fb, fw = fa_word(96, mode, 0, 0); eb, ew = en_word(48, mode, 0, 0, sub=True)
    Wd = max(fw, ew, 200) + 120
    body = (f'<g transform="translate({Wd/2-100:.1f} 30)">{mark_inner("v", mode)}</g>'
            f'<g transform="translate({(Wd-fw)/2:.1f} 325)">{fb}</g>'
            f'<g transform="translate({(Wd-ew)/2:.1f} 430)">{eb}</g>')
    files[f"lockup-stacked{sfx}.svg"] = svg(int(Wd), 500, body, "v", bg=bg)

# ۵) آیکن اپ (کاشی با زمینهٔ کِرم، و نسخهٔ ماسکیبل تمام‌صفحه)
def icon(size, maskable):
    sc = (0.62 if maskable else 0.70) * size / 200; off = (size - 200 * sc) / 2
    rad = 0 if maskable else size * .225
    bg = (f'<clipPath id="ck"><rect width="{size}" height="{size}" rx="{rad}"/></clipPath><g clip-path="url(#ck)">'
          f'<rect width="{size}" height="{size}" fill="#fff8e1"/>'
          f'<circle cx="{size*.9}" cy="{size*.06}" r="{size*.34}" fill="{TQ1}" fill-opacity=".30"/>'
          f'<circle cx="{size*.04}" cy="{size*.98}" r="{size*.38}" fill="{PU1}" fill-opacity=".32"/></g>')
    return svg(size, size, bg + f'<g transform="translate({off:.1f} {off:.1f}) scale({sc:.4f})">{mark_inner("i")}</g>', "i")
files["app-icon.svg"] = icon(512, False)
files["app-icon-maskable.svg"] = icon(512, True)

for n, c in files.items(): (OUT / n).write_text(c, encoding="utf-8")
print(len(files), "svg files")
