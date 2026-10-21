#!/usr/bin/env python3
"""WorkPlays – szablon grafiki „Oferta tygodnia” (1080x1350, 4:5).

Domyślny (zatwierdzony) wariant: b – karta-bilet z akcentami bursztyn/koral/fiolet.
Warianty a i c zostały jako alternatywy.

Użycie:
    python3 oferta_template.py --json oferta.json --out plik.png [--all-formats] [--variant a|b|c]
    (bez --json renderuje przykładową ofertę; --all-formats dodatkowo zapisuje
     <plik>_4x5.png, <plik>_1x1.png (LinkedIn) i <plik>_9x16.png (TikTok/Stories))

Dane oferty (JSON):
    {"title": "Texture Artist", "company": "Fool's Theory", "level": "Regular / Senior",
     "project": "The Witcher 3: Wild Hunt – Songs of the Past",
     "salary": "13 000 – 20 500 zł", "salary_note": "miesięcznie",
     "location": "Bielsko-Biała", "contract": "umowa na czas określony",
     "tags": ["Substance", "ZBrush", "PBR"],
     "week_label": "tydzień 44"}      # opcjonalne, pokazuje się po prawej od plakietki
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
NAVY = (12, 20, 44)
NAVY2 = (18, 30, 66)
NAVY3 = (28, 42, 88)
GREEN = (112, 238, 142)
GREEN_DARK = (46, 160, 86)
WHITE = (247, 248, 252)
MUTED = (160, 172, 200)
AMBER = (255, 196, 61)
CORAL = (255, 122, 89)
VIOLET = (154, 132, 255)
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "logo_alpha.png")


_WEIGHT_FALLBACK = {"ExtraBold": "Bold", "SemiBold": "Medium", "Black": "Bold"}


def font(size, weight="Bold", italic=False):
    name = f"Poppins-{weight}{'Italic' if italic else ''}.ttf"
    path = os.path.join(FONT_DIR, name)
    if not os.path.exists(path):
        weight = _WEIGHT_FALLBACK.get(weight, "Regular")
        path = os.path.join(FONT_DIR, f"Poppins-{weight}{'Italic' if italic else ''}.ttf")
    return ImageFont.truetype(path, size)


def text_w(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(d, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(d, t, f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(d, s, max_w, start, min_size=56, weight="Bold", max_lines=2):
    """Zmniejsza font, aż tekst mieści się w max_lines wierszach."""
    size = start
    while size > min_size:
        f = font(size, weight)
        if len(wrap(d, s, f, max_w)) <= max_lines:
            return f
        size -= 4
    return font(min_size, weight)


def fit_line(d, s, max_w, start, min_size=48, weight="Bold"):
    """Jedna linia: zmniejsza font, aż tekst zmieści się w max_w."""
    size = start
    while size > min_size and text_w(d, s, font(size, weight)) > max_w:
        size -= 4
    return font(size, weight)


def gradient_bg(top=NAVY, bottom=(8, 12, 30), glow=True):
    img = Image.new("RGB", (W, H), top)
    px = img.load()
    for y in range(H):
        t = y / H
        px_row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = px_row
    if glow:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse((W - 520, -420, W + 380, 480), fill=(112, 238, 142, 70))
        gd.ellipse((-380, H - 420, 420, H + 380), fill=(80, 120, 255, 50))
        g = g.filter(ImageFilter.GaussianBlur(160))
        img = Image.alpha_composite(img.convert("RGBA"), g).convert("RGB")
    return img


def diagonal_lines(img, color=(112, 238, 142, 40), step=170, width=2, angle=28):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    dx = math.tan(math.radians(angle)) * H
    for x in range(-int(dx) - step, W + step, step):
        d.line([(x, H), (x + dx, 0)], fill=color, width=width)
    return Image.alpha_composite(img.convert("RGBA"), layer)


def paste_logo(img, x, y, height=72):
    logo = Image.open(LOGO).convert("RGBA")
    r = height / logo.height
    logo = logo.resize((int(logo.width * r), height), Image.LANCZOS)
    img.alpha_composite(logo, (x, y))


class Layer:
    """Rysowanie półprzezroczystych kształtów na osobnej warstwie, potem alpha_composite."""
    def __init__(self, img):
        self.img = img
        self.layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.layer)
    def done(self):
        self.img.alpha_composite(self.layer)
        return ImageDraw.Draw(self.img)


def rrect(img, box, radius, fill=None, outline=None, width=2):
    L = Layer(img)
    L.d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    return L.done()


def arrow(d, x, y, size=22, color=NAVY, width=5):
    d.line([(x, y), (x + size, y)], fill=color, width=width)
    d.line([(x + size - 12, y - 12), (x + size, y), (x + size - 12, y + 12)], fill=color, width=width, joint="curve")


def pill(d, x, y, s, f, fill, fg, pad_x=34, pad_y=16, outline=None, img=None):
    tw = text_w(d, s, f)
    bb = d.textbbox((0, 0), s, font=f)
    th = bb[3] - bb[1]
    h = th + pad_y * 2
    box = (x, y, x + tw + pad_x * 2, y + h)
    if img is not None:
        d = rrect(img, box, h // 2, fill=fill, outline=outline, width=3)
    else:
        d.rounded_rectangle(box, radius=h // 2, fill=fill, outline=outline, width=3)
    d.text((x + pad_x, y + pad_y - bb[1]), s, font=f, fill=fg)
    return tw + pad_x * 2, h


def skew_label(img, x, y, s, f, fill=GREEN, fg=NAVY, pad=(40, 16), angle=-6):
    """Lekko przekręcona plakietka."""
    d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + pad[0] * 2, bb[3] - bb[1] + pad[1] * 2
    lab = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lab)
    ld.rounded_rectangle((30, 30, 30 + w, 30 + h), radius=18, fill=fill)
    ld.text((30 + pad[0] - bb[0], 30 + pad[1] - bb[1]), s, font=f, fill=fg)
    lab = lab.rotate(-angle, resample=Image.BICUBIC, expand=False)
    img.alpha_composite(lab, (x - 30, y - 30))
    return w, h


# ----------------------------------------------------------------- VARIANT A
def render_a(o):
    """Duża liczba. Skośne linie w tle, pensja jako bohater, CTA jako przycisk."""
    img = gradient_bg()
    img = diagonal_lines(img)
    d = ImageDraw.Draw(img)
    M = 80
    paste_logo(img, M, 72, 70)
    # etykieta
    skew_label(img, M, 215, "OFERTA TYGODNIA", font(34, "ExtraBold"), angle=-4)

    # tytuł
    y = 340
    tf = fit_font(d, o["title"], W - 2 * M, 112, 56, "ExtraBold")
    for ln in wrap(d, o["title"], tf, W - 2 * M):
        d.text((M, y), ln, font=tf, fill=WHITE)
        y += tf.size * 1.08
    y += 10
    sub = f"{o['company']}  ·  {o['level']}"
    sf = font(40, "Medium")
    d.text((M, y), sub, font=sf, fill=MUTED)
    y += 72

    # projekt
    if o.get("project"):
        pf = font(32, "SemiBold")
        lines = wrap(d, o["project"], pf, W - 2 * M - 48)
        box_h = 28 + len(lines) * 42 + 28 + 30
        d = rrect(img, (M, y, W - M, y + box_h), 22, fill=(255, 255, 255, 16), outline=(112, 238, 142, 130), width=2)
        d.text((M + 28, y + 22), "PROJEKT", font=font(20, "SemiBold"), fill=GREEN)
        yy = y + 56
        for ln in lines:
            d.text((M + 28, yy), ln, font=pf, fill=WHITE)
            yy += 42
        y += box_h + 44

    # pensja – bohater
    salf = fit_line(d, o["salary"], W - 2 * M, 108, 56, "ExtraBold")
    d.text((M, y), o["salary"], font=salf, fill=GREEN)
    y += salf.size + 6
    d.text((M, y), o.get("salary_note", "miesięcznie"), font=font(30, "Medium"), fill=MUTED)
    y += 76

    # chipy
    cf = font(28, "Medium")
    x = M
    for s in [o["location"], o["contract"]] + o.get("tags", [])[:2]:
        if not s:
            continue
        if x + text_w(d, s, cf) + 52 > W - M:
            break
        w, h = pill(d, x, y, s, cf, fill=(255, 255, 255, 26), fg=WHITE, pad_x=26, pad_y=12, img=img)
        x += w + 14
    y += 150

    # CTA
    cy = max(y, H - 230)
    bf = font(40, "Bold")
    s_cta = "Aplikuj na workplays.it"
    tw = text_w(d, s_cta, bf)
    bb = d.textbbox((0, 0), s_cta, font=bf)
    bh = bb[3] - bb[1] + 44
    d.rounded_rectangle((M, cy, M + tw + 84 + 50, cy + bh), radius=bh // 2, fill=GREEN)
    d.text((M + 42, cy + 22 - bb[1]), s_cta, font=bf, fill=NAVY)
    arrow(d, M + tw + 42 + 22, cy + bh // 2, size=32, color=NAVY, width=6)
    return img


# ----------------------------------------------------------------- VARIANT B
def render_b(o, _card_h=None):
    """Karta-bilet: jasna karta na tle, perforacja, zielony pasek po lewej."""
    if _card_h is None:
        # pierwszy przebieg tylko mierzy wysokość treści
        _, used = render_b(o, _card_h=0)
        return render_b(o, _card_h=used)
    img = gradient_bg(glow=False)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse((W - 560, -460, W + 420, 520), fill=(255, 122, 89, 95))   # koralowa poświata
    gd.ellipse((-420, H - 520, 460, H + 420), fill=(154, 132, 255, 85))  # fioletowa poświata
    gd.ellipse((-200, -300, 600, 420), fill=(112, 238, 142, 45))         # zielona
    img = Image.alpha_composite(img.convert("RGBA"), g.filter(ImageFilter.GaussianBlur(170)))
    img = diagonal_lines(img, color=(255, 255, 255, 14), step=120, width=1)
    d = ImageDraw.Draw(img)
    M = 64
    paste_logo(img, M + 8, 70, 66)
    lf = font(28, "SemiBold")
    d.text((W - M - text_w(d, "workplays.it", lf) - 8, 90), "workplays.it", font=lf, fill=MUTED)

    # karta
    cx0, cy0, cx1 = M, 200, W - M
    cy1 = (cy0 + _card_h + 56) if _card_h else H - 120
    cy1 = int(min(cy1, H - 120))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((cx0 + 10, cy0 + 24, cx1 + 10, cy1 + 24), radius=36, fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(img)
    d = rrect(img, (cx0, cy0, cx1, cy1), 36, fill=NAVY2 + (255,), outline=(112, 238, 142, 110), width=2)
    # grzbiet karty: gradient zieleń → bursztyn → koral
    spine = Image.new("RGBA", (18, cy1 - cy0), (0, 0, 0, 0))
    sp = spine.load()
    stops = [GREEN, AMBER, CORAL]
    for yy in range(spine.height):
        t = yy / (spine.height - 1) * (len(stops) - 1)
        i = min(int(t), len(stops) - 2)
        f = t - i
        c = tuple(int(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * f) for k in range(3)) + (255,)
        for xx in range(18):
            sp[xx, yy] = c
    mask = Image.new("L", spine.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 17, spine.height - 1), radius=9, fill=255)
    ImageDraw.Draw(mask).rectangle((9, 0, 17, spine.height - 1), fill=255)
    img.paste(spine, (cx0, cy0), mask)
    d = ImageDraw.Draw(img)

    px = cx0 + 60
    # etykieta
    pill(d, px, cy0 + 48, "OFERTA TYGODNIA", font(26, "ExtraBold"), fill=AMBER, fg=NAVY, pad_x=28, pad_y=12)
    # numer tygodnia / data po prawej
    wk = o.get("week_label", "")
    if wk:
        wf = font(24, "Medium")
        d.text((cx1 - 50 - text_w(d, wk, wf), cy0 + 60), wk, font=wf, fill=MUTED)

    y = cy0 + 150
    tf = fit_font(d, o["title"], cx1 - px - 50, 96, 52, "ExtraBold")
    for ln in wrap(d, o["title"], tf, cx1 - px - 50):
        d.text((px, y), ln, font=tf, fill=WHITE)
        y += tf.size * 1.08
    y += 8
    d.text((px, y), o["company"], font=font(42, "SemiBold"), fill=GREEN)
    y += 56
    d.text((px, y), o["level"], font=font(30, "Medium"), fill=MUTED)
    y += 70

    if o.get("project"):
        pf = font(28, "Medium")
        d.text((px, y), "Projekt", font=font(22, "SemiBold"), fill=MUTED)
        y += 34
        for ln in wrap(d, o["project"], pf, cx1 - px - 50):
            d.text((px, y), ln, font=pf, fill=WHITE)
            y += 38
        y += 30

    # perforacja
    y += 6
    L = Layer(img)
    for xx in range(px, cx1 - 50, 26):
        L.d.line([(xx, y), (xx + 12, y)], fill=(255, 255, 255, 70), width=3)
    d = L.done()
    d.ellipse((cx0 - 22 + 9, y - 22, cx0 + 22 + 9, y + 22), fill=NAVY)
    d.ellipse((cx1 - 22, y - 22, cx1 + 22, y + 22), fill=NAVY)
    y += 50

    salf = fit_line(d, o["salary"], cx1 - px - 50, 84, 52, "ExtraBold")
    d.text((px, y), o["salary"], font=salf, fill=GREEN)
    y += salf.size + 2
    d.text((px, y), o.get("salary_note", "miesięcznie") + "  ·  " + o["location"], font=font(28, "Medium"), fill=MUTED)
    y += 64
    cf = font(24, "Medium")
    x = px
    chips = [(o["contract"], (255, 255, 255, 90), WHITE, None)] + [
        (t, VIOLET + (0,), VIOLET, (154, 132, 255, 46)) for t in o.get("tags", [])[:3]
    ]
    for s, outline, fg, fill in chips:
        if not s:
            continue
        if x + text_w(d, s, cf) + 44 > cx1 - 60:
            break
        w, h = pill(d, x, y, s, cf, fill=fill, fg=fg, pad_x=22, pad_y=10, outline=outline, img=img)
        x += w + 12
    y += 60
    used = y - cy0

    # CTA w karcie
    bf = font(34, "Bold")
    s_cta = "Aplikuj na workplays.it"
    tw = text_w(d, s_cta, bf)
    bb = d.textbbox((0, 0), s_cta, font=bf)
    bh = bb[3] - bb[1] + 40
    d.rounded_rectangle((px, y, px + tw + 70 + 50, y + bh), radius=bh // 2, fill=GREEN)
    d.text((px + 35, y + 20 - bb[1]), s_cta, font=bf, fill=NAVY)
    arrow(d, px + tw + 35 + 20, y + bh // 2, size=28, color=NAVY, width=5)
    used = y + bh - cy0
    if _card_h == 0:
        return img, used
    # stopka
    ff = font(24, "Medium")
    s_f = "Codziennie nowe oferty z gamedevu  ·  workplays.it"
    d.text(((W - text_w(d, s_f, ff)) // 2, H - 76), s_f, font=ff, fill=MUTED)
    return img


# ----------------------------------------------------------------- VARIANT C
def render_c(o):
    """Split: granat / zieleń. Największy kontrast w feedzie."""
    img = gradient_bg(glow=False)
    img = diagonal_lines(img, color=(255, 255, 255, 12), step=140, width=1)
    d = ImageDraw.Draw(img)
    M = 80
    paste_logo(img, M, 72, 70)
    pill(d, M, 196, "OFERTA TYGODNIA", font(28, "ExtraBold"), fill=GREEN, fg=NAVY, pad_x=28, pad_y=12)

    y = 300
    tf = fit_font(d, o["title"], W - 2 * M, 118, 56, "ExtraBold")
    for ln in wrap(d, o["title"], tf, W - 2 * M):
        d.text((M, y), ln, font=tf, fill=WHITE)
        y += tf.size * 1.06
    y += 14
    d.text((M, y), o["company"], font=font(46, "SemiBold"), fill=WHITE)
    y += 62
    sub = o["level"]
    if o.get("project"):
        sub += "  ·  " + o["project"]
    sf = font(28, "Medium")
    for ln in wrap(d, sub, sf, W - 2 * M)[:2]:
        d.text((M, y), ln, font=sf, fill=MUTED)
        y += 40

    # dolny zielony blok ze skosem – zaczyna się pod treścią
    split = max(y + 70, 640)
    d.polygon([(0, split + 70), (W, split), (W, H), (0, H)], fill=GREEN)
    # grupa pensja + chipy + CTA wyśrodkowana pionowo w zielonym bloku
    group_h = 118 + 40 + 74 + 60 + 90 + 90
    y = split + 70 + max(40, (H - split - 70 - group_h) // 2)
    salf = fit_line(d, o["salary"], W - 2 * M, 104, 56, "ExtraBold")
    d.text((M, y), o["salary"], font=salf, fill=NAVY)
    y += salf.size + 4
    d.text((M, y), o.get("salary_note", "miesięcznie"), font=font(30, "Medium"), fill=(20, 60, 40))
    y += 74
    cf = font(26, "SemiBold")
    x = M
    for s in [o["location"], o["contract"]] + o.get("tags", [])[:2]:
        if not s:
            continue
        if x + text_w(d, s, cf) + 48 > W - M:
            break
        w, h = pill(d, x, y, s, cf, fill=None, fg=NAVY, pad_x=24, pad_y=10, outline=NAVY)
        x += w + 12
    # CTA
    y += 60 + 90
    bf = font(40, "ExtraBold")
    s = "workplays.it"
    d.rounded_rectangle((M, y, M + text_w(d, s, bf) + 84, y + 80), radius=40, fill=NAVY)
    d.text((M + 42, y + 16), s, font=bf, fill=GREEN)
    ax = M + text_w(d, s, bf) + 110
    d.text((ax, y + 8), "Aplikuj", font=font(32, "SemiBold"), fill=NAVY)
    arrow(d, ax + text_w(d, "Aplikuj", font(32, "SemiBold")) + 16, y + 38, size=30, color=NAVY)
    return img


RENDERERS = {"a": render_a, "b": render_b, "c": render_c}

SAMPLE = {
    "title": "Texture Artist",
    "company": "Fool's Theory",
    "level": "Regular / Senior",
    "project": "The Witcher 3: Wild Hunt – Songs of the Past (we współpracy z CD PROJEKT RED)",
    "salary": "13 000 – 20 500 zł",
    "salary_note": "miesięcznie",
    "location": "Bielsko-Biała",
    "contract": "umowa na czas określony",
    "tags": ["Substance Painter", "PBR"],
}


def export_formats(img, base):
    """Dodatkowe formaty: 1:1 (LinkedIn/FB) i 9:16 (TikTok/Stories) z tej samej grafiki."""
    img = img.convert("RGB")
    img.save(base + "_4x5.png", optimize=True)
    # 1:1 – przycięcie od góry z zachowaniem logo i dołu: skalujemy w dół i dokładamy tło
    sq = Image.new("RGB", (1080, 1080), NAVY)
    r = img.resize((864, 1080), Image.LANCZOS)
    sq.paste(r, (108, 0))
    sq.save(base + "_1x1.png", optimize=True)
    # 9:16 – dokładamy tło góra/dół
    tall = gradient_bg(glow=False).convert("RGB").resize((1080, 1920))
    tall.paste(img, (0, 285))
    tall.save(base + "_9x16.png", optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="b", choices=list(RENDERERS))
    ap.add_argument("--out", default="oferta.png")
    ap.add_argument("--json")
    ap.add_argument("--all-formats", action="store_true")
    a = ap.parse_args()
    data = SAMPLE if not a.json else json.load(open(a.json, encoding="utf-8"))
    img = RENDERERS[a.variant](data)
    img.convert("RGB").save(a.out, optimize=True)
    if a.all_formats:
        export_formats(img, os.path.splitext(a.out)[0])
    print("ok", a.out)
