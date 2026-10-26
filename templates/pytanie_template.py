#!/usr/bin/env python3
"""WorkPlays – grafika „Pytanie tygodnia” (1080x1350, 4:5).

Użycie:
    python3 pytanie_template.py --json pytanie.json --out plik.png

JSON:
    {"question": "Unity, Unreal czy Godot na pierwszą pracę w gamedevie?",
     "options": ["Unity", "Unreal Engine", "Godot", "Silnik bez znaczenia – liczy się portfolio"],
     "cta": "A Ty? Napisz numer w komentarzu",
     "mascot": "../assets/programista_mysliciel.png",   # oryginalny PNG, wklejany bez zmian
     "badge": "PYTANIE TYGODNIA"}
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
GREEN = (112, 238, 142)
WHITE = (247, 248, 252)
MUTED = (160, 172, 200)
NAVY_CARD = (22, 34, 74)
AMBER = (255, 196, 61)
CORAL = (255, 122, 89)
VIOLET = (154, 132, 255)
ACCENTS = [GREEN, AMBER, CORAL, VIOLET]
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "logo_alpha.png")


def font(size, weight="Bold"):
    p = os.path.join(FONT_DIR, f"Poppins-{weight}.ttf")
    if not os.path.exists(p):
        p = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
    return ImageFont.truetype(p, size)


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


def background():
    img = Image.new("RGBA", (W, H))
    top, bot = (20, 32, 70), (8, 12, 30)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,)
        for x in range(W):
            px[x, y] = c
    # soft glow on a separate layer
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(420, 0, -12):
        a = int(26 * (1 - r / 420))
        gd.ellipse((W - 260 - r, H - 380 - r, W - 260 + r, H - 380 + r), fill=GREEN + (a,))
    return Image.alpha_composite(img, glow)


def render(o):
    img = background()
    d = ImageDraw.Draw(img)
    # header: logo + url
    logo = Image.open(LOGO).convert("RGBA")
    lw = 230
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, (70, 70))
    fu = font(34, "Medium")
    d.text((W - 70 - tw(d, "workplays.it", fu), 78), "workplays.it", font=fu, fill=MUTED)

    # badge
    fb = font(30, "Bold")
    badge = o.get("badge", "PYTANIE TYGODNIA")
    bw = tw(d, badge, fb) + 56
    d.rounded_rectangle((70, 180, 70 + bw, 236), radius=28, fill=AMBER)
    d.text((98, 186), badge, font=fb, fill=(12, 20, 44))

    # question
    size = 76
    while True:
        fq = font(size, "Bold")
        lines = wrap(d, o["question"], fq, W - 140)
        if len(lines) <= 3 or size <= 52:
            break
        size -= 4
    y = 272
    for ln in lines:
        d.text((70, y), ln, font=fq, fill=WHITE)
        y += int(size * 1.18)

    # mascot (original PNG, only scaled)
    m = o.get("mascot")
    mascot_left = W
    if m:
        mp = m if os.path.isabs(m) else os.path.normpath(os.path.join(HERE, m))
        mi = Image.open(mp).convert("RGBA")
        bb = mi.getbbox()
        mi = mi.crop(bb)
        mh = o.get("mascot_height", 600)
        mi = mi.resize((int(mi.width * mh / mi.height), mh), Image.LANCZOS)
        mx = W - mi.width - 30
        my = H - 110 - mh
        img.alpha_composite(mi, (mx, my))
        mascot_left = mx

    # options
    oy = y + 40
    card_w = min(640, mascot_left - 70 - 10)
    fo = font(36, "SemiBold")
    fn = font(38, "Bold")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    rows = []
    for i, opt in enumerate(o["options"]):
        ol = wrap(d, opt, fo, card_w - 120)
        ch = max(96, 36 + len(ol) * 46)
        rows.append((oy, ch, ol, ACCENTS[i % 4]))
        ld.rounded_rectangle((70, oy, 70 + card_w, oy + ch), radius=22, fill=NAVY_CARD + (235,))
        oy += ch + 18
    img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)
    for i, (ry, ch, ol, col) in enumerate(rows):
        d.rounded_rectangle((70, ry, 70 + card_w, ry + ch), radius=22, outline=col, width=3)
        cx, cy = 70 + 52, ry + ch // 2
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=col)
        n = str(i + 1)
        d.text((cx - tw(d, n, fn) / 2, cy - 27), n, font=fn, fill=(12, 20, 44))
        ty = ry + (ch - len(ol) * 46) // 2 - 4
        for ln in ol:
            d.text((70 + 104, ty), ln, font=fo, fill=WHITE)
            ty += 46

    # CTA footer
    fc = font(40, "Bold")
    cta = o.get("cta", "A Ty? Napisz numer w komentarzu")
    d.text((70, H - 92), cta, font=fc, fill=GREEN)
    return img.convert("RGB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    render(json.load(open(a.json))).save(a.out)
    print("ok", a.out)
