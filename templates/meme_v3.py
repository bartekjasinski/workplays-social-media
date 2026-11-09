#!/usr/bin/env python3
"""WorkPlays – memy v3 (1080x1350, 4:5): motywy z gier, każdy z innym układem i paletą.

Zasada: maskotka to zawsze oryginalny PNG z assets/ (tylko skalowanie / odbicie lustrzane).

Użycie:
  python3 meme_v3.py --json mem.json --out mem.png

Motywy ("theme"):
  chat         – telefon z czatem (koralowo-fioletowy gradient, pieczątka, maskotka obok telefonu)
                 {"theme":"chat","caption":"... *słowo* ...","contact":"Rekruterka · Studio",
                  "messages":[["them","..."],["me","...","Wyświetlono 18:31"],["typing"]],
                  "stamp":"WIDEŁKI: 404","mascot":{...}}
  achievements – ciemny ekran gry z wyskakującymi achievementami (pikselowy caption)
                 {"theme":"achievements","caption":"...","toasts":[{"label":"...","title":"...","note":"..."}],
                  "footer":"3/3 · NAGRODA: CRUNCH","mascot":{...}}
  quest        – dziennik questów RPG na pastelowej zieleni
                 {"theme":"quest","caption":"...","quest":"Zostań juniorem","sub":"...",
                  "objectives":[{"text":"...","state":"done|current|locked"}],"reward":"...","mascot":{...}}
  W captionie *gwiazdki* oznaczają słowa wyróżnione kolorem.
  mascot: {"image": "../assets/x.png", "height": 600, "x": 0.8, "bottom": 0, "flip": false}
"""
import argparse, json, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
GF = "/usr/share/fonts/truetype/google-fonts"
FD = os.path.join(HERE, "fonts")
NAVY = (12, 20, 44)
NAVY2 = (22, 34, 74)
GREEN = (112, 238, 142)
AMBER = (255, 196, 61)
CORAL = (255, 122, 89)
VIOLET = (154, 132, 255)
WHITE = (247, 248, 252)
MUTED = (150, 160, 190)


def pop(size, w="Bold"):
    p = os.path.join(GF, f"Poppins-{w}.ttf")
    return ImageFont.truetype(p if os.path.exists(p) else os.path.join(GF, "Poppins-Bold.ttf"), size)


def pixel(size):
    return ImageFont.truetype(os.path.join(FD, "PressStart2P-Regular.ttf"), size)


def mono(size, bold=False):
    return ImageFont.truetype(os.path.join(FD, f"JetBrainsMono-{'Bold' if bold else 'Regular'}.ttf"), size)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(d, s, f, mw):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if tw(d, t.replace("*", ""), f) <= mw:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def rich_line(d, x, y, line, f, base, hi, marker=None):
    """Rysuje linię, w której *słowa* mają kolor hi (albo marker pod spodem)."""
    parts, on = [], False
    for i, chunk in enumerate(line.split("*")):
        if chunk:
            parts.append((chunk, on))
        on = not on
    for chunk, h in parts:
        w = tw(d, chunk, f)
        if h and marker:
            d.rounded_rectangle((x - 6, y + f.size * 0.28, x + w + 6, y + f.size * 1.18), radius=8, fill=marker)
        d.text((x, y), chunk, font=f, fill=(hi if (h and not marker) else base))
        x += w
    return x


def line_w(d, line, f):
    return tw(d, line.replace("*", ""), f)


def caption_block(d, cap, f, x, y, mw, base, hi, lh=1.18, align="left", marker=None):
    # wyróżnienie przechodzi przez łamanie linii: domknij/otwórz gwiazdki per linia
    lines = wrap(d, cap, f, mw)
    fixed, open_ = [], False
    for ln in lines:
        s = ("*" if open_ else "") + ln
        if s.count("*") % 2 == 1:
            s += "*"
            open_ = True
        else:
            open_ = False
        fixed.append(s.replace("**", ""))
    for ln in fixed:
        lx = x if align == "left" else x + (mw - line_w(d, ln, f)) // 2
        rich_line(d, lx, y, ln, f, base, hi, marker)
        y += int(f.size * lh)
    return y


def fit_font(d, cap, fn, mw, start, stop, max_lines):
    s = start
    while s > stop:
        if len(wrap(d, cap, fn(s), mw)) <= max_lines:
            return fn(s)
        s -= 2
    return fn(stop)


def lin_grad(c1, c2, diag=True):
    g = Image.new("RGB", (W, H))
    px = g.load()
    for y in range(H):
        for x in range(0, W):
            t = ((x / W) * 0.45 + (y / H) * 0.55) if diag else y / H
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return g.convert("RGBA")


def glow(img, cx, cy, r, color, alpha=110):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (alpha,))
    return Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(r // 2)))


def shadow(img, box, radius=28, off=(10, 18), blur=22, alpha=120):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(lay).rounded_rectangle((x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]), radius=radius, fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(blur)))


def paste_mascot(img, m):
    a = Image.open(os.path.join(HERE, m["image"]) if not os.path.isabs(m["image"]) else m["image"]).convert("RGBA")
    if m.get("flip"):
        a = a.transpose(Image.FLIP_LEFT_RIGHT)
    mh = int(m.get("height", 620))
    a = a.resize((round(a.width * mh / a.height), mh), Image.LANCZOS)
    x = int(W * m.get("x", 0.8) - a.width / 2)
    y = H - a.height - int(m.get("bottom", 0))
    img.alpha_composite(a, (x, y))
    return (x, y, x + a.width, y + a.height)


def site_pill(img, fg=NAVY, bg=GREEN, pos="br", y_off=0):
    d = ImageDraw.Draw(img)
    f = pop(28, "Bold")
    s = "workplays.it"
    w = tw(d, s, f) + 44
    x = W - w - 40 if pos == "br" else 40
    y = H - 84 - y_off
    d.rounded_rectangle((x, y, x + w, y + 54), radius=27, fill=bg)
    d.text((x + 22, y + 8), s, font=f, fill=fg)


# ---------------------------------------------------------------- chat
def render_chat(o):
    img = lin_grad((255, 140, 100), (130, 110, 250))
    img = glow(img, 900, 250, 260, (255, 210, 120), 90)
    d = ImageDraw.Draw(img)
    cap = o["caption"]
    f = fit_font(d, cap, lambda s: pop(s, "Bold"), W - 140, 70, 46, 3)
    y = caption_block(d, cap, f, 70, 64, W - 140, NAVY, NAVY, marker=WHITE)
    # telefon – osobna warstwa, lekko obrócona
    pw, ph = 600, 1000
    ph_l = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0))
    pd = ImageDraw.Draw(ph_l)
    pd.rounded_rectangle((20, 20, 20 + pw, 20 + ph), radius=70, fill=(16, 18, 28))
    pd.rounded_rectangle((36, 36, 4 + pw, 4 + ph), radius=56, fill=(24, 27, 42))
    sx, sy = 36, 36
    # notch
    pd.rounded_rectangle((20 + pw // 2 - 70, 46, 20 + pw // 2 + 70, 76), radius=15, fill=(10, 10, 16))
    # nagłówek rozmowy
    pd.line((sx, 190, 4 + pw, 190), fill=(44, 48, 70), width=2)
    pd.ellipse((sx + 34, 104, sx + 104, 174), fill=GREEN)
    fa = pop(36, "Bold")
    pd.text((sx + 69 - tw(pd, "R", fa) // 2, 112), "R", font=fa, fill=NAVY)
    pd.text((sx + 124, 106), o.get("contact", "Rekruterka · Studio"), font=pop(30, "Bold"), fill=WHITE)
    pd.text((sx + 124, 144), o.get("status", "online"), font=pop(22, "Medium"), fill=GREEN)
    # dymki
    by = 230
    fb = pop(29, "Medium")
    maxw = 400
    hl_box = None
    for msg in o["messages"]:
        kind = msg[0]
        if kind == "typing":
            bx1 = 4 + pw - 30
            pd.rounded_rectangle((bx1 - 130, by, bx1, by + 70), radius=35, fill=GREEN)
            for i in range(3):
                cx = bx1 - 95 + i * 32
                pd.ellipse((cx - 9, by + 26, cx + 9, by + 44), fill=NAVY if i == 1 else (40, 80, 70))
            by += 100
            continue
        text = msg[1]
        lines = wrap(pd, text, fb, maxw)
        bw = max(tw(pd, l, fb) for l in lines) + 56
        bh = len(lines) * 40 + 34
        if kind == "me":
            bx1 = 4 + pw - 30
            bx0 = bx1 - bw
            pd.rounded_rectangle((bx0, by, bx1, by + bh), radius=30, fill=GREEN)
            col = NAVY
        else:
            bx0 = sx + 30
            bx1 = bx0 + bw
            pd.rounded_rectangle((bx0, by, bx1, by + bh), radius=30, fill=(48, 53, 80))
            col = WHITE
        ty = by + 15
        for l in lines:
            pd.text((bx0 + 28, ty), l, font=fb, fill=col)
            ty += 40
        if len(msg) > 2 and msg[2] == "!":
            hl_box = (bx0, by, bx1, by + bh)
        by += bh + 14
        if len(msg) > 2 and msg[2] not in ("!",):
            fm = pop(20, "Medium")
            pd.text((bx1 - tw(pd, msg[2], fm), by - 6), msg[2], font=fm, fill=MUTED)
            by += 28
        by += 16
    if hl_box:  # czerwone zakreślenie dymka
        x0, y0, x1, y1 = hl_box
        pd.ellipse((x0 - 22, y0 - 16, x1 + 22, y1 + 16), outline=(235, 52, 52), width=6)
    # pole wpisywania
    pd.rounded_rectangle((sx + 30, ph - 110, 4 + pw - 30, ph - 40), radius=35, fill=(40, 44, 66))
    pd.text((sx + 64, ph - 94), "Napisz kwotę…", font=pop(26, "Medium"), fill=MUTED)
    rot = ph_l.rotate(o.get("tilt", 4), resample=Image.BICUBIC, expand=True)
    px0, py0 = 40, max(y + 20, 330)
    img = shadow(img, (px0 + 40, py0 + 40, px0 + pw, py0 + ph), radius=70, off=(18, 26), blur=30, alpha=110)
    img.alpha_composite(rot, (px0, py0))
    # pieczątka
    if o.get("stamp"):
        st = o["stamp"]
        fs = pixel(34)
        tmp = Image.new("RGBA", (10, 10))
        sw = tw(ImageDraw.Draw(tmp), st, fs) + 60
        sl = Image.new("RGBA", (sw + 20, 110), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sl)
        sd.rounded_rectangle((10, 10, sw + 10, 100), radius=14, outline=(225, 40, 40), width=7, fill=(255, 255, 255, 235))
        sd.text((40, 38), st, font=fs, fill=(225, 40, 40))
        sl = sl.rotate(-12, resample=Image.BICUBIC, expand=True)
        sx_, sy_ = o.get("stamp_pos", [600, 1000])
        img.alpha_composite(sl, (sx_, sy_))
    paste_mascot(img, o["mascot"])
    site_pill(img)
    return img


# ---------------------------------------------------------------- achievements
def trophy_icon(d, cx, cy, r, color):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    # czerwona flaga: maszt + trójkąt
    d.rectangle((cx - r * 0.38, cy - r * 0.55, cx - r * 0.28, cy + r * 0.6), fill=NAVY)
    d.polygon([(cx - r * 0.28, cy - r * 0.55), (cx + r * 0.52, cy - r * 0.3), (cx - r * 0.28, cy - r * 0.02)], fill=(230, 45, 45))


def render_achievements(o):
    img = Image.new("RGBA", (W, H), (9, 11, 22, 255))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 36):
        d.line((x, 0, x, H), fill=(18, 22, 40), width=1)
    for y in range(0, H, 36):
        d.line((0, y, W, y), fill=(18, 22, 40), width=1)
    img = glow(img, 540, 700, 380, (120, 70, 200), 120)
    img = glow(img, 900, 1150, 260, AMBER, 70)
    d = ImageDraw.Draw(img)
    cap = o["caption"].upper()
    f = fit_font(d, cap, pixel, W - 120, 40, 26, 5)
    y = caption_block(d, cap, f, 60, 80, W - 120, WHITE, CORAL, lh=1.55, align="center")
    y += 40
    tf = pop(40, "Bold")
    lf = mono(22, True)
    nf = pop(22, "Medium")
    for i, t in enumerate(o["toasts"]):
        x0 = 50 + i * 30
        x1 = x0 + 920
        h = 150
        img = shadow(img, (x0, y, x1, y + h), radius=75, off=(0, 14), blur=18, alpha=150)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x0, y, x1, y + h), radius=75, fill=(30, 34, 52), outline=(70, 76, 110), width=2)
        trophy_icon(d, x0 + 75, y + 75, 52, AMBER)
        d.text((x0 + 150, y + 26), t.get("label", "ACHIEVEMENT ODBLOKOWANY"), font=lf, fill=GREEN)
        tsz = 40
        while tw(d, t["title"], pop(tsz, "Bold")) > x1 - x0 - 190 and tsz > 26:
            tsz -= 2
        d.text((x0 + 150, y + 56 + (40 - tsz) // 2), t["title"], font=pop(tsz, "Bold"), fill=WHITE)
        if t.get("note"):
            d.text((x1 - 40 - tw(d, t["note"], nf), y + 28), t["note"], font=nf, fill=AMBER)
        y += h + 26
    if o.get("footer"):
        ff = pixel(24)
        d.text((60, y + 20), o["footer"], font=ff, fill=AMBER)
        # pasek postępu
        d.rounded_rectangle((60, y + 70, 560, y + 100), radius=6, outline=AMBER, width=3)
        d.rounded_rectangle((66, y + 76, 554, y + 94), radius=4, fill=CORAL)
    paste_mascot(img, o["mascot"])
    site_pill(img, fg=NAVY, bg=AMBER)
    return img


# ---------------------------------------------------------------- quest
def render_quest(o):
    img = Image.new("RGBA", (W, H), GREEN + (255,))
    d = ImageDraw.Draw(img)
    for k in range(-H, W, 46):  # ukośne paski
        d.line((k, 0, k + H, H), fill=(100, 222, 128), width=16)
    cap = o["caption"]
    f = fit_font(d, cap, lambda s: pop(s, "Bold"), W - 120, 66, 44, 3)
    y = caption_block(d, cap, f, 60, 60, W - 120, NAVY, NAVY, marker=WHITE)
    y += 30
    px0, px1 = 50, 800
    # wysokość panelu
    rows = o["objectives"]
    ph = 250 + len(rows) * 62 + 150
    img = shadow(img, (px0, y, px1, y + ph), radius=24, off=(14, 18), blur=0, alpha=255)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((px0, y, px1, y + ph), radius=24, fill=NAVY, outline=AMBER, width=5)
    for cx, cy in [(px0 + 18, y + 18), (px1 - 30, y + 18), (px0 + 18, y + ph - 30), (px1 - 30, y + ph - 30)]:
        d.rectangle((cx, cy, cx + 12, cy + 12), fill=AMBER)
    d.text((px0 + 50, y + 44), "QUEST LOG", font=pixel(24), fill=AMBER)
    d.text((px0 + 50, y + 86), o["quest"], font=pop(50, "Bold"), fill=WHITE)
    d.text((px0 + 50, y + 152), o.get("sub", ""), font=pop(24, "Medium"), fill=MUTED)
    ry = y + 210
    of = pop(30, "Medium")
    for r in rows:
        st = r.get("state", "done")
        bx = px0 + 52
        if st == "current":
            d.rounded_rectangle((px0 + 24, ry - 8, px1 - 24, ry + 52), radius=12, fill=(70, 34, 40))
            d.polygon([(bx, ry + 8), (bx + 22, ry + 22), (bx, ry + 36)], fill=CORAL)
            d.text((bx + 44, ry + 2), r["text"], font=pop(30, "Bold"), fill=CORAL)
        elif st == "locked":
            d.rounded_rectangle((bx, ry + 18, bx + 26, ry + 40), radius=4, fill=(90, 100, 130))
            d.arc((bx + 4, ry + 4, bx + 22, ry + 28), 180, 360, fill=(90, 100, 130), width=4)
            d.text((bx + 44, ry + 2), r["text"], font=of, fill=(90, 100, 130))
        else:
            d.rounded_rectangle((bx, ry + 8, bx + 30, ry + 38), radius=6, outline=GREEN, width=3)
            d.line((bx + 6, ry + 23, bx + 13, ry + 31, bx + 25, ry + 13), fill=GREEN, width=5)
            d.text((bx + 44, ry + 2), r["text"], font=of, fill=MUTED)
            tl = tw(d, r["text"], of)
            d.line((bx + 44, ry + 24, bx + 44 + tl, ry + 24), fill=MUTED, width=2)
        ry += 62
    # pasek postępu segmentowy
    ry += 20
    n = len(rows)
    done = sum(1 for r in rows if r.get("state", "done") == "done")
    d.text((px0 + 50, ry), f"POSTĘP {done + 1}/{n}", font=pixel(20), fill=WHITE)
    sx0, sw, gap = px0 + 50, (px1 - px0 - 100 - (n - 1) * 8) / n, 8
    for i, r in enumerate(rows):
        st = r.get("state", "done")
        col = GREEN if st == "done" else CORAL if st == "current" else (44, 54, 90)
        x = sx0 + i * (sw + gap)
        d.rectangle((x, ry + 40, x + sw, ry + 64), fill=col)
    if o.get("reward"):
        d.text((px0 + 50, ry + 86), "Nagroda: ", font=pop(28, "Bold"), fill=AMBER)
        d.text((px0 + 50 + tw(d, "Nagroda: ", pop(28, "Bold")), ry + 86), o["reward"], font=pop(28, "Medium"), fill=WHITE)
    paste_mascot(img, o["mascot"])
    site_pill(img, fg=GREEN, bg=NAVY)
    return img


RENDER = {"chat": render_chat, "achievements": render_achievements, "quest": render_quest}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    o = json.load(open(a.json, encoding="utf-8"))
    RENDER[o["theme"]](o).convert("RGB").save(a.out, "PNG")
    print("ok", a.out)
