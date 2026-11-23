#!/usr/bin/env python3
"""WorkPlays – plansza tekstowa BEZ maskotki (1080x1350): duże pytanie + 2–4 numerowane odpowiedzi.

Użycie:
    python3 plansza_template.py --json plansza.json --out plik.png

JSON:
    {"question": "Co bardziej szkodzi karierze?", "emoji": "🤔",
     "options": ["Zbyt wąski stack", "Zła firma", "Brak zmian"],
     "bg": [34, 22, 52],            # jednolite spokojne tło (RGB)
     "accent": [112, 238, 142],     # kolor numerów
     "footer": "workplays.it"}
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
WHITE = (247, 248, 252)
MUTED = (175, 180, 205)
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
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


def emoji_img(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


def render(o):
    bg = tuple(o.get("bg", [34, 22, 52]))
    acc = tuple(o.get("accent", [112, 238, 142]))
    img = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(img)
    M = 96
    maxw = W - 2 * M

    # logo (bez podpisu), lewy górny róg
    logo = Image.open(LOGO).convert("RGBA")
    lw = 230
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, (M, 90))

    # pytanie – największy możliwy rozmiar mieszczący się w 4 liniach
    for qs in range(92, 50, -2):
        fq = font(qs)
        ql = wrap(d, o["question"], fq, maxw)
        if len(ql) <= 4:
            break
    y = 270
    lh = int(qs * 1.22)
    for i, line in enumerate(ql):
        d.text((M, y), line, font=fq, fill=WHITE)
        if i == len(ql) - 1 and o.get("emoji"):
            em = emoji_img(o["emoji"], int(qs * 0.95))
            x = M + tw(d, line, fq) + 22
            if x + em.width > W - M:
                y += lh
                x = M
            img.alpha_composite(em, (x, y + int(qs * 0.18)))
        y += lh

    # odpowiedzi
    y += 70
    fo = font(50, "Medium")
    fn = font(58)
    for i, opt in enumerate(o["options"], 1):
        num = f"{i}."
        d.text((M, y), num, font=fn, fill=acc)
        ol = wrap(d, opt, fo, maxw - 90)
        yy = y + 4
        for line in ol:
            d.text((M + 90, yy), line, font=fo, fill=WHITE)
            yy += 64
        y = max(yy, y + 70) + 38

    # stopka
    ff = font(36, "Medium")
    foot = o.get("footer", "workplays.it")
    d.text((W - M - tw(d, foot, ff), H - 120), foot, font=ff, fill=MUTED)
    return img.convert("RGB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    render(json.load(open(a.json, encoding="utf-8"))).save(a.out)
    print(a.out)
