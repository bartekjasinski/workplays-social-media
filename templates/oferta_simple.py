#!/usr/bin/env python3
"""WorkPlays – prosta grafika „Oferta tygodnia” (spokojne granatowe tło, mało koloru).

Użycie:
    python3 oferta_simple.py --json oferta.json --out wt-oferta.png
    -> zapisuje <out>_4x5.png (1080x1350), <out>_1x1.png (1080x1080), <out>_9x16.png (1080x1920)

JSON: {"title": "...", "company": "...", "salary": "15 000 – 22 000 zł",
       "salary_note": "miesięcznie, B2B", "details": "Wrocław · B2B · Unreal Engine"}
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont

BG = (16, 22, 42)
WHITE = (247, 248, 252)
MUTED = (165, 172, 195)
AMBER = (255, 196, 61)
GREEN = (112, 238, 142)
LINE = (44, 54, 86)
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "logo_alpha.png")


def font(size, weight="Bold"):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"Poppins-{weight}.ttf"), size)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(d, s, f, max_w):
    lines, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if tw(d, t, f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(o, W, H):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    M = 96
    maxw = W - 2 * M
    s = 1.0 if H >= 1300 else 0.86  # 1:1 trochę ciaśniej

    logo = Image.open(LOGO).convert("RGBA")
    lw = 230
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)

    # blok treści – liczymy wysokość, potem centrujemy w pionie
    fl = font(int(34 * s), "Medium")
    ft = font(int(84 * s))
    fc = font(int(46 * s), "Medium")
    fs = font(int(92 * s))
    fn = font(int(36 * s), "Regular")
    fd = font(int(38 * s), "Regular")
    title = wrap(d, o["title"], ft, maxw)
    gap = int(40 * s)
    blocks = [("label", 50 * s), ("gap", gap)]
    th = len(title) * int(98 * s)
    content_h = 50 * s + gap + th + int(70 * s) + gap * 2 + 2 + gap * 2 + int(110 * s) + int(50 * s) + gap + int(50 * s)
    y = max(int(230 * s), (H - content_h) // 2)

    img.alpha_composite(logo, (M, int(90 * s) if H < 1900 else 140))

    d.text((M, y), "OFERTA TYGODNIA", font=fl, fill=GREEN)
    y += int(50 * s) + gap
    for line in title:
        d.text((M, y), line, font=ft, fill=WHITE)
        y += int(98 * s)
    d.text((M, y + int(18 * s)), o["company"], font=fc, fill=MUTED)
    y += int(70 * s) + gap * 2
    d.line((M, y, W - M, y), fill=LINE, width=2)
    y += gap * 2
    d.text((M, y), o["salary"], font=fs, fill=AMBER)
    y += int(115 * s)
    d.text((M, y), o.get("salary_note", ""), font=fn, fill=MUTED)
    y += int(50 * s) + gap
    for line in wrap(d, o.get("details", ""), fd, maxw):
        d.text((M, y), line, font=fd, fill=WHITE)
        y += int(52 * s)

    fu = font(40, "Medium")
    foot = "Aplikuj na workplays.it"
    fy = H - (130 if H < 1900 else 220)
    d.text((M, fy), foot, font=fu, fill=WHITE)
    d.line((M, fy + 62, M + tw(d, foot, fu), fy + 62), fill=GREEN, width=4)
    return img.convert("RGB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    o = json.load(open(a.json, encoding="utf-8"))
    base = a.out[:-4] if a.out.endswith(".png") else a.out
    for tag, (w, h) in {"4x5": (1080, 1350), "1x1": (1080, 1080), "9x16": (1080, 1920)}.items():
        p = f"{base}_{tag}.png"
        render(o, w, h).save(p)
        print(p)
