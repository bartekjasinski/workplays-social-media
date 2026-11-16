#!/usr/bin/env python3
"""WorkPlays – grafiki v4: nowe układy, każdy z inną paletą i innym kadrem maskotki.

Zasada brand hero: maskotka to zawsze oryginalny PNG z assets/ – tylko skalowanie
i kadrowanie ramką (popiersie w kółku / postać ucięta krawędzią). Bez przerysowań.

Użycie:
  python3 meme_v4.py --json plik.json --out plik.png [--all-formats]

Motywy ("theme"):
  inbox     – jasna skrzynka mailowa (kremowo-bursztynowa), pieczątka, maskotka wychodzi zza krawędzi
  creator   – ekran tworzenia postaci (fiolet), maskotka na podeście, paski umiejętności
  versus    – dwa panele „W CV / W rzeczywistości” na koralu, maskotka jako awatar w UI gildii
  tabs      – pytanie jako karty przeglądarki do zamknięcia (pastelowa zieleń)
  terminal  – oferta jako terminal / odebrany sygnał (czerń + fosforowa zieleń); --all-formats: 4x5, 1x1, 9x16
Przykłady JSON: media/2026-11-23/*.json
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GF = "/usr/share/fonts/truetype/google-fonts"
FD = os.path.join(HERE, "fonts")
LOGO = os.path.join(HERE, "logo_alpha.png")

NAVY = (12, 20, 44)
GREEN = (112, 238, 142)
AMBER = (255, 196, 61)
CORAL = (255, 122, 89)
VIOLET = (154, 132, 255)
WHITE = (250, 250, 252)
RED = (228, 48, 48)


def pop(size, w="Bold"):
    p = os.path.join(GF, f"Poppins-{w}.ttf")
    return ImageFont.truetype(p if os.path.exists(p) else os.path.join(GF, "Poppins-Bold.ttf"), size)


def mono(size, bold=False):
    return ImageFont.truetype(os.path.join(FD, f"JetBrainsMono-{'Bold' if bold else 'Regular'}.ttf"), size)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(d, s, f, mw):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if tw(d, t, f) <= mw:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def fit(d, s, mw, start, mn, lines, fn):
    size = start
    while size > mn and len(wrap(d, s, fn(size), mw)) > lines:
        size -= 2
    return fn(size)


def vgrad(w, h, c1, c2):
    g = Image.new("RGBA", (w, h))
    dr = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(1, h - 1)
        dr.line([(0, y), (w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,))
    return g


def shadow(img, box, r=28, off=(0, 18), blur=22, alpha=110):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]), radius=r, fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(blur)))


def layer_rect(img, box, fill, r=24, outline=None, width=0):
    """Półprzezroczyste prostokąty na osobnej warstwie."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)
    return Image.alpha_composite(img, lay)


def mascot_img(path, height):
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    a = Image.open(p).convert("RGBA")
    a = a.crop(a.getbbox())
    return a.resize((round(a.width * height / a.height), height), Image.LANCZOS)


def avatar(path, d, ring=None, bg=(236, 239, 246), frac=0.5):
    """Popiersie w kółku: kadr górnej części oryginalnego PNG (bez zmian w rysunku)."""
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    a = Image.open(p).convert("RGBA")
    a = a.crop(a.getbbox())
    side = a.width
    crop = a.crop((0, 0, side, min(a.height, int(a.height * frac) if frac else side)))
    s = max(crop.size)
    sq = Image.new("RGBA", (s, s), bg + (255,))
    sq.alpha_composite(crop, ((s - crop.width) // 2, 0))
    sq = sq.resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d, d), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(sq, (0, 0), m)
    if ring:
        ImageDraw.Draw(out).ellipse((2, 2, d - 3, d - 3), outline=ring, width=6)
    return out


def logo(img, x, y, h=56):
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA")
        lg = lg.resize((round(lg.width * h / lg.height), h), Image.LANCZOS)
        img.alpha_composite(lg, (x, y))


def stamp(img, text, center, color, angle=-12, size=46):
    f = mono(size, True)
    d0 = ImageDraw.Draw(img)
    w = tw(d0, text, f) + 56
    h = size + 44
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((3, 3, w - 4, h - 4), radius=12, outline=color + (235,), width=6)
    sd.text((28, 16), text, font=f, fill=color + (235,))
    st = st.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(st, (int(center[0] - st.width / 2), int(center[1] - st.height / 2)))


def caption_block(img, text, y, color, mw=960, start=62, lines=3, upper=True):
    d = ImageDraw.Draw(img)
    s = text.upper() if upper else text
    f = fit(d, s, mw, start, 38, lines, lambda z: pop(z, "Bold"))
    for ln in wrap(d, s, f, mw):
        d.text(((img.width - tw(d, ln, f)) // 2, y), ln, font=f, fill=color)
        y += int(f.size * 1.18)
    return y


# ---------------------------------------------------------------- inbox
def r_inbox(o):
    W, H = 1080, 1350
    img = vgrad(W, H, (253, 247, 234), (255, 226, 160))
    d = ImageDraw.Draw(img)
    y = caption_block(img, o["caption"], 70, NAVY)
    # okno poczty
    x0, y0, x1 = 60, y + 40, 1020
    rows = o["rows"]
    rh = 150
    y1 = y0 + 96 + rh * len(rows) + 24
    img = shadow(img, (x0, y0, x1, y1), alpha=70)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0, x1, y1), radius=26, fill=(255, 255, 255))
    d.rounded_rectangle((x0, y0, x1, y0 + 84), radius=26, fill=(244, 245, 249))
    d.rectangle((x0, y0 + 60, x1, y0 + 84), fill=(244, 245, 249))
    d.text((x0 + 36, y0 + 22), o.get("folder", "Odebrane"), font=pop(32, "Bold"), fill=NAVY)
    d.rounded_rectangle((x1 - 330, y0 + 20, x1 - 30, y0 + 64), radius=22, fill=(255, 255, 255), outline=(222, 225, 234), width=2)
    d.text((x1 - 306, y0 + 28), "Szukaj w poczcie", font=pop(22, "Regular"), fill=(160, 166, 184))
    ry = y0 + 96
    for i, r in enumerate(rows):
        if i:
            d.line((x0 + 30, ry, x1 - 30, ry), fill=(236, 238, 243), width=2)
        hl = r.get("highlight")
        ac = r.get("color", [90, 100, 130])
        d.ellipse((x0 + 32, ry + 34, x0 + 112, ry + 114), fill=tuple(ac))
        d.text((x0 + 72 - tw(d, r["letter"], pop(36)) // 2, ry + 50), r["letter"], font=pop(36, "Bold"), fill=WHITE)
        d.text((x0 + 138, ry + 26), r["from"], font=pop(28, "Bold" if r.get("unread") else "Medium"), fill=NAVY)
        tf = pop(24, "Bold" if r.get("unread") else "Regular")
        d.text((x1 - 36 - tw(d, r["time"], tf), ry + 30), r["time"], font=tf, fill=(RED if hl else (120, 126, 148)))
        sf = pop(26, "Bold" if r.get("unread") else "Medium")
        subj = r["subject"]
        while tw(d, subj, sf) > x1 - x0 - 200 and len(subj) > 4:
            subj = subj[:-2]
        if subj != r["subject"]:
            subj = subj.rstrip() + "…"
        d.text((x0 + 138, ry + 66), subj, font=sf, fill=(30, 34, 50))
        pf = pop(22, "Regular")
        prev = r.get("preview", "")
        d.text((x0 + 138, ry + 104), prev, font=pf, fill=(130, 136, 156))
        if r.get("unread"):
            d.ellipse((x0 + 14, ry + 68, x0 + 26, ry + 80), fill=(40, 110, 255))
        if hl:
            d.ellipse((x0 + 124, ry + 58, x1 - 160, ry + 108), outline=RED, width=5)
        ry += rh
    # maskotka wychodzi zza dolnej krawędzi (kadr ramką)
    m = o["mascot"]
    a = mascot_img(m["image"], m.get("height", 900))
    mx = int(W * m.get("x", 0.74) - a.width / 2)
    img.alpha_composite(a, (mx, H - a.height + m.get("cut", 260)))
    if o.get("stamp"):
        stamp(img, o["stamp"], tuple(o.get("stamp_pos", [300, y1 + 120])), RED, o.get("stamp_angle", -10))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((44, H - 92, 300, H - 40), radius=26, fill=NAVY)
    d.text((70, H - 84), "workplays.it", font=pop(28, "Bold"), fill=GREEN)
    return img


# ---------------------------------------------------------------- creator
def r_creator(o):
    W, H = 1080, 1350
    img = vgrad(W, H, (34, 20, 84), (88, 52, 170))
    # delikatna siatka
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for x in range(0, W, 54):
        ld.line((x, 0, x, H), fill=(255, 255, 255, 14))
    for yy in range(0, H, 54):
        ld.line((0, yy, W, yy), fill=(255, 255, 255, 14))
    img = Image.alpha_composite(img, lay)
    y = caption_block(img, o["caption"], 64, WHITE)
    d = ImageDraw.Draw(img)
    d.text((60, y + 22), o.get("screen", "TWORZENIE POSTACI"), font=mono(26, True), fill=AMBER)
    top = y + 72
    # lewy panel z postacią
    lp = (60, top, 470, H - 120)
    img = layer_rect(img, lp, (255, 255, 255, 26), r=28, outline=(255, 255, 255, 60), width=2)
    d = ImageDraw.Draw(img)
    cx = (lp[0] + lp[2]) // 2
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx - 170, lp[3] - 150, cx + 170, lp[3] - 80), fill=AMBER + (150,))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(14)))
    m = o["mascot"]
    a = mascot_img(m["image"], m.get("height", 560))
    img.alpha_composite(a, (cx - a.width // 2, lp[3] - 115 - a.height))
    d = ImageDraw.Draw(img)
    d.text((lp[0] + 28, lp[1] + 24), "KLASA", font=mono(22), fill=(200, 190, 255))
    cf = fit(d, o["klass"], lp[2] - lp[0] - 56, 34, 22, 1, lambda z: pop(z, "Bold"))
    d.text((lp[0] + 28, lp[1] + 54), o["klass"], font=cf, fill=WHITE)
    d.text((lp[0] + 28, lp[1] + 100), o.get("level", "POZIOM 1"), font=mono(24, True), fill=GREEN)
    # prawy panel – umiejętności
    rp = (500, top, 1020, H - 120)
    img = layer_rect(img, rp, (10, 8, 30, 150), r=28, outline=(255, 255, 255, 50), width=2)
    d = ImageDraw.Draw(img)
    d.text((rp[0] + 30, rp[1] + 26), o.get("skills_title", "WYMAGANE UMIEJĘTNOŚCI"), font=mono(24, True), fill=(200, 190, 255))
    sy = rp[1] + 78
    for s in o["skills"]:
        d.text((rp[0] + 30, sy), s, font=pop(26, "Medium"), fill=WHITE)
        by = sy + 40
        d.rounded_rectangle((rp[0] + 30, by, rp[2] - 30, by + 14), radius=7, fill=(255, 255, 255, 40))
        d.rounded_rectangle((rp[0] + 30, by, rp[2] - 30, by + 14), radius=7, fill=AMBER)
        sy += 74
    # czerwony warunek
    req = o.get("red")
    if req:
        f = pop(26, "Bold")
        d.rounded_rectangle((rp[0] + 24, sy + 6, rp[2] - 24, sy + 66), radius=14, fill=(255, 92, 92, 255))
        d.text((rp[0] + 44, sy + 19), req, font=f, fill=WHITE)
        sy += 80
    d.text((rp[0] + 30, rp[3] - 56), o.get("points", "Punkty do rozdania: 0"), font=mono(24, True), fill=GREEN)
    d.text((W - 60 - tw(d, "workplays.it", pop(28)), H - 82), "workplays.it", font=pop(28, "Bold"), fill=GREEN)
    logo(img, 60, H - 90, 48)
    return img


# ---------------------------------------------------------------- versus
def r_versus(o):
    W, H = 1080, 1350
    img = vgrad(W, H, (255, 138, 104), (255, 200, 120))
    y = caption_block(img, o["caption"], 60, NAVY, start=58)
    d = ImageDraw.Draw(img)
    # panel 1: kartka CV, lekko przechylona
    cv = o["cv"]
    pw, ph = 860, 330
    page = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(page)
    pd.rectangle((0, 0, pw - 1, ph - 1), fill=(255, 255, 255))
    pd.rectangle((0, 0, 14, ph), fill=NAVY)
    pd.text((50, 30), cv["title"], font=pop(26, "Bold"), fill=(150, 156, 176))
    pd.text((50, 70), cv["role"], font=pop(40, "Bold"), fill=NAVY)
    py = 136
    for b in cv["bullets"]:
        pd.text((50, py), "•  " + b, font=pop(27, "Regular"), fill=(40, 44, 60))
        py += 44
    page = page.rotate(-2.2, expand=True, resample=Image.BICUBIC)
    px, py0 = (W - page.width) // 2, y + 70
    img = shadow(img, (px + 20, py0 + 20, px + page.width - 20, py0 + page.height - 10), r=4, alpha=90)
    img.alpha_composite(page, (px, py0))
    d = ImageDraw.Draw(img)
    tag = lambda x, yy, t, bg, fg: (d.rounded_rectangle((x, yy, x + tw(d, t, pop(26)) + 44, yy + 52), radius=26, fill=bg),
                                    d.text((x + 22, yy + 9), t, font=pop(26, "Bold"), fill=fg))
    tag(70, py0 - 26, o.get("tag1", "W CV"), NAVY, WHITE)
    # panel 2: UI gildii
    gy = py0 + page.height + 60
    gb = (70, gy, 1010, H - 110)
    img = shadow(img, gb, alpha=120)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(gb, radius=22, fill=(18, 20, 34), outline=(214, 170, 70), width=4)
    tag(70, gy - 26, o.get("tag2", "W RZECZYWISTOŚCI"), (214, 170, 70), NAVY)
    g = o["guild"]
    d.text((gb[0] + 36, gy + 46), g["name"], font=pop(34, "Bold"), fill=(240, 205, 110))
    d.text((gb[2] - 36 - tw(d, g["online"], mono(24, True)), gy + 56), g["online"], font=mono(24, True), fill=GREEN)
    ry = gy + 110
    av = avatar(o["mascot"]["image"], 96, ring=(240, 205, 110), bg=(60, 64, 96), frac=o["mascot"].get("frac", 0.52))
    for i, (nick, rank) in enumerate(g["members"]):
        if i == 0:
            img = layer_rect(img, (gb[0] + 20, ry - 10, gb[2] - 20, ry + 104), (240, 205, 110, 40), r=16)
            img.alpha_composite(av, (gb[0] + 36, ry))
            d = ImageDraw.Draw(img)
            d.text((gb[0] + 150, ry + 10), nick, font=pop(30, "Bold"), fill=WHITE)
            d.text((gb[0] + 150, ry + 52), rank, font=mono(24, True), fill=(240, 205, 110))
            ry += 126
        else:
            d.ellipse((gb[0] + 66, ry + 12, gb[0] + 84, ry + 30), fill=GREEN if i < 3 else (90, 96, 120))
            d.text((gb[0] + 150, ry), nick, font=pop(27, "Medium"), fill=(210, 214, 228))
            d.text((gb[2] - 40 - tw(d, rank, mono(22)), ry + 6), rank, font=mono(22), fill=(150, 156, 180))
            ry += 50
    d.rounded_rectangle((W - 320, H - 92, W - 44, H - 40), radius=26, fill=NAVY)
    d.text((W - 294, H - 84), "workplays.it", font=pop(28, "Bold"), fill=GREEN)
    return img


# ---------------------------------------------------------------- tabs (pytanie)
def r_tabs(o):
    W, H = 1080, 1350
    img = vgrad(W, H, (196, 248, 210), (112, 238, 142))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((44, 46, 300, 112), radius=33, fill=NAVY)
    logo(img, 66, 56, 46)
    d.rounded_rectangle((W - 330, 56, W - 60, 104), radius=24, fill=NAVY)
    d.text((W - 306, 64), o.get("badge", "PYTANIE TYGODNIA"), font=pop(24, "Bold"), fill=GREEN)
    y = 150
    f = fit(d, o["question"], 960, 66, 44, 3, lambda z: pop(z, "Bold"))
    for ln in wrap(d, o["question"], f, 960):
        d.text((60, y), ln, font=f, fill=NAVY)
        y += int(f.size * 1.15)
    # okno przeglądarki z kartami
    bx0, by0, bx1, by1 = 60, y + 40, 1020, H - 130
    img = shadow(img, (bx0, by0, bx1, by1), alpha=80)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=24, fill=(250, 251, 253))
    d.rounded_rectangle((bx0, by0, bx1, by0 + 70), radius=24, fill=(226, 230, 238))
    d.rectangle((bx0, by0 + 46, bx1, by0 + 70), fill=(226, 230, 238))
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        d.ellipse((bx0 + 28 + i * 34, by0 + 24, bx0 + 50 + i * 34, by0 + 46), fill=c)
    d.rounded_rectangle((bx0 + 150, by0 + 16, bx1 - 30, by0 + 56), radius=20, fill=(255, 255, 255))
    d.text((bx0 + 172, by0 + 22), o.get("url", "oferta-pracy-gamedev.html"), font=mono(20), fill=(130, 136, 156))
    accents = [GREEN, AMBER, CORAL, VIOLET]
    ty = by0 + 100
    for i, opt in enumerate(o["options"]):
        ac = accents[i % 4]
        th = o.get("tab_h", 128)
        d.rounded_rectangle((bx0 + 30, ty, bx1 - 30, ty + th), radius=18, fill=(255, 255, 255), outline=ac, width=4)
        d.rounded_rectangle((bx0 + 30, ty, bx0 + 54, ty + th), radius=10, fill=ac)
        d.rectangle((bx0 + 42, ty, bx0 + 54, ty + th), fill=ac)
        d.text((bx0 + 80, ty + th // 2 - 30), f"{i + 1}", font=pop(40, "Bold"), fill=NAVY)
        of = fit(d, opt, 560, 34, 24, 1, lambda z: pop(z, "Bold"))
        d.text((bx0 + 140, ty + th // 2 - 24), opt, font=of, fill=NAVY)
        # przycisk zamknięcia karty
        cx, cy = bx1 - 92, ty + th // 2
        d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=(240, 242, 247))
        d.line((cx - 10, cy - 10, cx + 10, cy + 10), fill=(90, 96, 120), width=5)
        d.line((cx - 10, cy + 10, cx + 10, cy - 10), fill=(90, 96, 120), width=5)
        ty += th + 22
    # maskotka – popiersie w „kamerce” na rogu okna
    m = o["mascot"]
    av = avatar(m["image"], m.get("size", 250), ring=NAVY, bg=(255, 236, 190), frac=m.get("frac", 0.5))
    img.alpha_composite(av, (bx1 - av.width + 30, by1 - av.height + 60))
    d = ImageDraw.Draw(img)
    d.text((60, H - 96), o.get("cta", "A Ty? Napisz numer w komentarzu"), font=pop(36, "Bold"), fill=NAVY)
    return img


# ---------------------------------------------------------------- terminal (oferta)
def r_terminal(o, W=1080, H=1350):
    img = Image.new("RGBA", (W, H), (8, 12, 10, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for yy in range(0, H, 6):
        ld.line((0, yy, W, yy), fill=(112, 238, 142, 10))
    ld.ellipse((-W, -H // 2, 2 * W, H + H // 2), fill=(112, 238, 142, 18))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(2)))
    d = ImageDraw.Draw(img)
    s = H / 1350 if H < 1350 else 1.0
    M = 64
    top = 60 if H <= 1350 else 260
    if H < 1350:
        top = 44
    rs = 58 if H >= 1350 else 44
    logo(img, M, top, 50)
    wk = o.get("week_label", "")
    d.text((W - M - tw(d, wk, mono(24)), top + 12), wk, font=mono(24), fill=(112, 238, 142))
    y = top + 100
    d.text((M, y), "> " + o.get("signal", "SYGNAŁ ODEBRANY · OFERTA TYGODNIA"), font=mono(int(28 * max(s, .85)), True), fill=GREEN)
    y += int(62 * s) + 10
    tf = fit(d, o["title"], W - 2 * M, int(84 * max(s, .8)), 48, 2, lambda z: pop(z, "Bold"))
    for ln in wrap(d, o["title"], tf, W - 2 * M):
        d.text((M, y), ln, font=tf, fill=WHITE)
        y += int(tf.size * 1.1)
    y += 14
    d.text((M, y), o["company"], font=pop(int(40 * max(s, .85)), "Bold"), fill=GREEN)
    y += int(58 * max(s, .85))
    d.text((M, y), o["pitch"], font=pop(int(28 * max(s, .85)), "Medium"), fill=(190, 200, 196))
    y += int(64 * s) + 10
    # ramka z danymi
    rows = o["rows"]
    bh = rs * len(rows) + (40 if H >= 1350 else 24)
    img = layer_rect(img, (M, y, W - M, y + bh), (112, 238, 142, 22), r=14, outline=(112, 238, 142, 140), width=2)
    d = ImageDraw.Draw(img)
    ry = y + (22 if H >= 1350 else 12)
    for k, v in rows:
        d.text((M + 28, ry), k.ljust(9), font=mono(26, True), fill=GREEN)
        d.text((M + 230, ry), v, font=mono(26), fill=WHITE)
        ry += rs
    y += bh + int(44 * s)
    d.text((M, y), o.get("salary_label", "WIDEŁKI"), font=mono(24, True), fill=(160, 170, 166))
    y += 38
    sf = fit(d, o["salary"], W - 2 * M - (300 if (o.get("mascot") and H >= 1350) else 40), int(96 * max(s, .8)), 50, 1, lambda z: pop(z, "Bold"))
    d.text((M, y), o["salary"], font=sf, fill=AMBER)
    y += int(sf.size * 1.15)
    d.text((M, y), o["salary_note"], font=pop(28, "Medium"), fill=(190, 200, 196))
    y += int(66 * s) + 6
    tx = M
    for t in o.get("tags", []):
        lab = f"[{t}]"
        d.text((tx, y), lab, font=mono(24, True), fill=VIOLET)
        tx += tw(d, lab, mono(24, True)) + 20
    y += int(70 * s) + 10
    cta = o.get("cta", "Aplikuj na workplays.it")
    cf = pop(34, "Bold")
    d.rounded_rectangle((M, y, M + tw(d, cta, cf) + 64, y + 76), radius=38, fill=GREEN)
    d.text((M + 32, y + 14), cta, font=cf, fill=NAVY)
    m = o.get("mascot")
    if m and H >= 1350:
        a = mascot_img(m["image"], m.get("height", 470))
        img.alpha_composite(a, (W - a.width - m.get("right", 30), H - a.height - m.get("bottom", 40) - (260 if H > 1350 else 0)))
    if H > 1350:
        d = ImageDraw.Draw(img)
        d.text((M, H - 200), "Codziennie nowe oferty z gamedevu", font=pop(30, "Medium"), fill=(160, 170, 166))
    return img


R = {"inbox": r_inbox, "creator": r_creator, "versus": r_versus, "tabs": r_tabs, "terminal": r_terminal}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--all-formats", action="store_true")
    a = ap.parse_args()
    o = json.load(open(a.json, encoding="utf-8"))
    if a.all_formats and o["theme"] == "terminal":
        base = a.out[:-4] if a.out.endswith(".png") else a.out
        for suf, (w, h) in {"_4x5": (1080, 1350), "_1x1": (1080, 1080), "_9x16": (1080, 1920)}.items():
            r_terminal(o, w, h).convert("RGB").save(base + suf + ".png", optimize=True)
            print("ok", base + suf + ".png")
    else:
        R[o["theme"]](o).convert("RGB").save(a.out, optimize=True)
        print("ok", a.out)
