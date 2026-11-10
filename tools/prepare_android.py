#!/usr/bin/env python3
"""
بعد از `npx cap add android` اجرا شود (چند بار اجرا هم بی‌خطر است).
کارها: امضای release از متغیرهای محیطی، versionCode/versionName، آیکن، اسپلش، نام فارسی برنامه.
env: KEYSTORE_FILE KEYSTORE_PASSWORD KEY_ALIAS KEY_PASSWORD VERSION_CODE VERSION_NAME
"""
import os, re, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "android" / "app"
RES = APP / "src/main/res"
SRC_ICON = ROOT / "docs/icons/maskable-512.png"
if not APP.exists():
    sys.exit("android/ پیدا نشد؛ اول `npx cap add android` را اجرا کنید.")

# ---------- build.gradle ----------
g = APP / "build.gradle"
s = g.read_text(encoding="utf-8")
if "// SPENDBOOK-PATCH" not in s:
    signing = '''
    // SPENDBOOK-PATCH: امضا از متغیرهای محیطی
    signingConfigs {
        release {
            if (System.getenv("KEYSTORE_FILE")) {
                storeFile file(System.getenv("KEYSTORE_FILE"))
                storePassword System.getenv("KEYSTORE_PASSWORD")
                keyAlias System.getenv("KEY_ALIAS")
                keyPassword System.getenv("KEY_PASSWORD")
            }
        }
    }
'''
    s = s.replace("    defaultConfig {", signing + "    defaultConfig {", 1)
    s = re.sub(r"versionCode \d+", 'versionCode (System.getenv("VERSION_CODE") ?: "1").toInteger()', s, count=1)
    s = re.sub(r'versionName "[^"]*"', 'versionName (System.getenv("VERSION_NAME") ?: "1.0")', s, count=1)
    s = s.replace("        release {\n            minifyEnabled false",
                  "        release {\n            if (System.getenv(\"KEYSTORE_FILE\")) { signingConfig signingConfigs.release }\n            minifyEnabled false", 1)
    assert "signingConfig signingConfigs.release" in s, "anchor release{} not found"
    g.write_text(s, encoding="utf-8")
    print("build.gradle patched")

# ---------- icons ----------
src = Image.open(SRC_ICON).convert("RGBA")
bg = src.getpixel((2, 2))
bg_hex = "#%02x%02x%02x" % bg[:3]

def fg(px):  # لایهٔ جلوییِ شفاف؛ آیکن ۸۳٪ بوم تا داخل ناحیهٔ ایمن بماند
    c = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    k = int(px * 0.83)
    im = src.resize((k, k), Image.LANCZOS)
    c.paste(im, ((px - k) // 2, (px - k) // 2), im)
    return c

def legacy(px, round_=False):
    im = src.resize((px, px), Image.LANCZOS)
    mask = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(mask)
    if round_: d.ellipse((0, 0, px - 1, px - 1), fill=255)
    else: d.rounded_rectangle((0, 0, px - 1, px - 1), radius=int(px * .2), fill=255)
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0)); out.paste(im, (0, 0), mask)
    return out

dens = {"mdpi": (48, 108), "hdpi": (72, 162), "xhdpi": (96, 216), "xxhdpi": (144, 324), "xxxhdpi": (192, 432)}
for d, (leg, ad) in dens.items():
    m = RES / f"mipmap-{d}"; m.mkdir(parents=True, exist_ok=True)
    legacy(leg).save(m / "ic_launcher.png")
    legacy(leg, True).save(m / "ic_launcher_round.png")
    fg(ad).save(m / "ic_launcher_foreground.png")
(RES / "values/ic_launcher_background.xml").write_text(
    f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">{bg_hex}</color>\n</resources>\n', encoding="utf-8")
# لایهٔ برداریِ پیش‌فرض Capacitor (drawable-v24) را حذف کن تا PNG استفاده شود
v24 = RES / "drawable-v24/ic_launcher_foreground.xml"
if v24.exists(): v24.unlink()
for xml in ("ic_launcher.xml", "ic_launcher_round.xml"):
    p = RES / "mipmap-anydpi-v26" / xml
    p.write_text('<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                 '    <background android:drawable="@color/ic_launcher_background"/>\n'
                 '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n</adaptive-icon>\n', encoding="utf-8")

# ---------- splash: پس‌زمینهٔ کِرم + آیکن وسط ----------
cream = (255, 248, 225, 255)
n = 0
for p in RES.glob("drawable*/splash.png"):
    w, h = Image.open(p).size
    im = Image.new("RGBA", (w, h), cream)
    k = int(min(w, h) * 0.28)
    ic = src.resize((k, k), Image.LANCZOS)
    mask = Image.new("L", (k, k), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, k - 1, k - 1), radius=int(k * .22), fill=255)
    im.paste(ic, ((w - k) // 2, (h - k) // 2), mask)
    im.convert("RGB").save(p); n += 1
print("icons ok, splash files:", n)

# ---------- اعلان‌ها: آیکن کوچک تک‌رنگ + مجوزها در Manifest ----------
for d, px in {"mdpi": 24, "hdpi": 36, "xhdpi": 48, "xxhdpi": 72, "xxxhdpi": 96}.items():
    im = Image.new("RGBA", (px * 4, px * 4), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); r = px * 4 * .30
    c = px * 4 / 2
    dr.ellipse((c - r * 1.5, c - r, c - r * 1.5 + 2 * r, c + r), fill=(255, 255, 255, 255))
    dr.ellipse((c + r * 1.5 - 2 * r, c - r, c + r * 1.5, c + r), fill=(255, 255, 255, 255))
    out = RES / f"drawable-{d}"; out.mkdir(parents=True, exist_ok=True)
    im.resize((px, px), Image.LANCZOS).save(out / "ic_stat_notify.png")
mf = APP / "src/main/AndroidManifest.xml"
m = mf.read_text(encoding="utf-8")
for perm in ("POST_NOTIFICATIONS", "SCHEDULE_EXACT_ALARM", "RECEIVE_BOOT_COMPLETED", "VIBRATE"):
    line = f'<uses-permission android:name="android.permission.{perm}" />'
    if perm not in m:
        m = m.replace("</manifest>", f"    {line}\n</manifest>")
mf.write_text(m, encoding="utf-8")
print("notification icon + permissions ok")

# ---------- نام برنامه (fa: خرج‌نگار، بقیه: SpendBook) ----------
def strings(path, name):
    path.parent.mkdir(parents=True, exist_ok=True)
    s = path.read_text(encoding="utf-8") if path.exists() else '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n'
    if 'name="app_name"' in s:
        s = re.sub(r'(<string name="app_name">)[^<]*(</string>)', r"\g<1>%s\g<2>" % name, s)
    else:
        s = s.replace("</resources>", f'    <string name="app_name">{name}</string>\n</resources>')
    path.write_text(s, encoding="utf-8")
strings(RES / "values/strings.xml", "Dakhl o Kharj")
strings(RES / "values-fa/strings.xml", "دخل و خرج")
strings(RES / "values-ar/strings.xml", "دخل وخرج")
print("done")
