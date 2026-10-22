#!/usr/bin/env python3
"""WorkPlays – szablon memów v2 (1080x1350, 4:5). Bardziej „memowy” niż v1:
caption bezpośrednio na obrazku (gruby biały Poppins z czarnym obrysem),
scena na całą szerokość, dyskretne logo + hashtag w stopce.

Tryby:
  scene  – jeden obrazek (scena z maskotką) + caption góra (+ opcjonalnie dół)
  panels – 2 panele jeden pod drugim, każdy z etykietą (np. ❌ / ✅ albo „Oczekiwania / Rzeczywistość”)
  chat   – dialog w dymkach („Ja: / Szef:”) na górze, scena/maskotka pod spodem

Użycie:
  python3 meme_v2.py --json mem.json --out mem.png
  JSON:
    {"mode":"scene","image":"scene.png","top":"Kiedy rekruter pisze „oferta zdalna*”","bottom":"*3 dni w biurze"}
    {"mode":"panels","top":"Rozmowa rekrutacyjna","panels":[{"image":"a.png","label":"Oczekiwania"},{"image":"b.png","label":"Rzeczywistość"}]}
    {"mode":"chat","messages":[["Ja","Szefie, zagramy w statki?"],["Szef","OK."],["Ja","L4 !!!"]],"image":"scene.png"}
  Pola opcjonalne: "hashtag" (domyślnie #pracawgamedevie), "fit": "cover"|"contain" (domyślnie cover),
  "bg": kolor tła dla contain (domyślnie biały), "caption_pos": "top"|"bottom".
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
INTER_DIR = "/usr/share/fonts/opentype/inter"
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "logo_alpha.png")
GREEN = (112, 238, 142)
NAVY = (12, 20, 44)
BLACK = (10, 10, 12)
WHITE = (255, 255, 255)


def font(size, weight="Bold"):
    p = os.path.join(FONT_DIR, f"Poppins-{weight}.ttf")
    if not os.path.exists(p):
        p = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
    return ImageFont.truetype(p, size)


def font_black(size):
    """Najgrubszy dostępny krój pod memowe nagłówki."""
    for p in [os.path.join(INTER_DIR, "InterDisplay-Black.otf"), os.path.join(INTER_DIR, "Inter-Black.otf"),
              os.path.join(FONT_DIR, "Poppins-Bold.ttf")]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_w(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(d, s, f, max_w):
    out = []
    for para in s.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            t = (cur + " " + w).strip()
            if text_w(d, t, f) <= max_w:
                cur = t
            else:
                if cur:
                    out.append(cur)
                cur = w
        out.append(cur)
    return out


def fit(d, s, max_w, start, min_size, max_lines, fontfn=font):
    size = start
    while size > min_size:
        f = fontfn(size)
        if len(wrap(d, s, f, max_w)) <= max_lines:
            return f
        size -= 4
    return fontfn(min_size)


def cover(img, w, h, anchor=0.5):
    """Przycina obrazek do w×h zachowując proporcje; anchor 0..1 = gdzie trzymać środek w pionie."""
    r = max(w / img.width, h / img.height)
    im = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * anchor)
    return im.crop((x, y, x + w, y + h))


def contain(img, w, h, bg=WHITE):
    r = min(w / img.width, h / img.height)
    im = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), bg + (255,))
    out.alpha_composite(im.convert("RGBA"), ((w - im.width) // 2, (h - im.height) // 2))
    return out


def outlined_text(img, xy, s, f, fill=WHITE, stroke=BLACK, stroke_w=6, align="left", shadow=True):
    d = ImageDraw.Draw(img)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 4, xy[1] + 6), s, font=f, fill=(0, 0, 0, 160),
                                stroke_width=stroke_w, stroke_fill=(0, 0, 0, 160), align=align)
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(img)
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke_w, stroke_fill=stroke, align=align)


def caption_block(img, text, y, max_w=W - 120, start=78, min_size=44, max_lines=4, pos="top", center=True):
    """Caption memowy z obrysem. Zwraca wysokość zajętą."""
    d = ImageDraw.Draw(img)
    f = fit(d, text, max_w, start, min_size, max_lines, font_black)
    lines = wrap(d, text, f, max_w)
    lh = int(f.size * 1.12)
    total = lh * len(lines)
    if pos == "bottom":
        y = y - total
    for i, ln in enumerate(lines):
        x = (W - text_w(d, ln, f)) // 2 if center else 60
        outlined_text(img, (x, y + i * lh), ln, f, stroke_w=max(5, f.size // 12))
    return total


def footer(img, hashtag="#pracawgamedevie"):
    """Dyskretna stopka: logo w lewym dolnym rogu, hashtag w prawym – na półprzezroczystej podkładce."""
    bar_h = 86
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    # gradient zaciemnienia od dołu
    for i in range(bar_h + 60):
        a = int(170 * (i / (bar_h + 60)))
        ld.line([(0, H - bar_h - 60 + i), (W, H - bar_h - 60 + i)], fill=(0, 0, 0, a))
    img.alpha_composite(layer)
    logo = Image.open(LOGO).convert("RGBA")
    lh = 52
    logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
    img.alpha_composite(logo, (48, H - bar_h + (bar_h - lh) // 2))
    d = ImageDraw.Draw(img)
    f = font(28, "Medium")
    d.text((W - 48 - text_w(d, hashtag, f), H - bar_h + (bar_h - 34) // 2), hashtag, font=f, fill=GREEN)


def load_image(path, w, h, mode="cover", bg=WHITE, anchor=0.45):
    im = Image.open(path).convert("RGBA")
    if mode == "contain":
        return contain(im, w, h, bg)
    return cover(im, w, h, anchor)


# ------------------------------------------------------------------ scene
def render_scene(o):
    img = Image.new("RGBA", (W, H), BLACK + (255,))
    src = Image.open(o["image"])
    landscape = src.width / src.height > 1.15 and o.get("fit", "auto") == "auto"
    if landscape:
        # pozioma scena: caption na ciemnym pasie u góry, obrazek na całą szerokość, caption pod nim
        d = ImageDraw.Draw(img)
        # policz wysokość bloku, żeby wyśrodkować go w pionie nad stopką
        ih = round(W * src.height / src.width)
        block = ih
        ft = fb = None
        if o.get("top"):
            ft = fit(d, o["top"], W - 120, 72, 44, 3, font_black)
            block += len(wrap(d, o["top"], ft, W - 120)) * int(ft.size * 1.15) + 30
        if o.get("bottom"):
            fb = fit(d, o["bottom"], W - 120, 64, 40, 3, font_black)
            block += len(wrap(d, o["bottom"], fb, W - 120)) * int(fb.size * 1.15) + 30
        y = max(48, (H - 86 - block) // 2)
        if o.get("top"):
            f = ft
            lines = wrap(d, o["top"], f, W - 120)
            for ln in lines:
                d.text(((W - text_w(d, ln, f)) // 2, y), ln, font=f, fill=WHITE)
                y += int(f.size * 1.15)
            y += 30
        scene = load_image(o["image"], W, ih, "cover")
        img.alpha_composite(scene, (0, y))
        y += ih + 30
        if o.get("bottom"):
            d = ImageDraw.Draw(img)
            f = fb
            for ln in wrap(d, o["bottom"], f, W - 120):
                d.text(((W - text_w(d, ln, f)) // 2, y), ln, font=f, fill=WHITE)
                y += int(f.size * 1.15)
        footer(img, o.get("hashtag", "#pracawgamedevie"))
        return img
    scene = load_image(o["image"], W, H, "cover" if o.get("fit", "auto") == "auto" else o["fit"], tuple(o.get("bg", WHITE)), o.get("anchor", 0.45))
    img.alpha_composite(scene)
    if o.get("top"):
        # lekkie zaciemnienie góry, żeby biały tekst czytał się na jasnej scenie
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for i in range(360):
            ld.line([(0, i), (W, i)], fill=(0, 0, 0, int(150 * (1 - i / 360))))
        img.alpha_composite(layer)
        caption_block(img, o["top"], 56)
    if o.get("bottom"):
        caption_block(img, o["bottom"], H - 110, pos="bottom", start=64, max_lines=3)
    footer(img, o.get("hashtag", "#pracawgamedevie"))
    return img


# ------------------------------------------------------------------ panels
def render_panels(o):
    img = Image.new("RGBA", (W, H), BLACK + (255,))
    y = 0
    if o.get("top"):
        d = ImageDraw.Draw(img)
        f = fit(d, o["top"], W - 120, 56, 36, 2, font_black)
        lines = wrap(d, o["top"], f, W - 120)
        yy = 48
        for ln in lines:
            d.text(((W - text_w(d, ln, f)) // 2, yy), ln, font=f, fill=WHITE)
            yy += int(f.size * 1.15)
        y = yy + 28
    panels = o["panels"][:2]
    avail = H - y - 86
    gap = 10
    ph = (avail - gap) // len(panels)
    for i, p in enumerate(panels):
        py = y + i * (ph + gap)
        pim = load_image(p["image"], W, ph, p.get("fit", o.get("fit", "cover")), tuple(p.get("bg", WHITE)), p.get("anchor", 0.4))
        img.alpha_composite(pim, (0, py))
        if p.get("label"):
            d = ImageDraw.Draw(img)
            f = font_black(60)
            lab = p["label"]
            tw = text_w(d, lab, f)
            # etykieta w rogu panelu na zielonej/białej plakietce
            col = p.get("label_color")
            fill = tuple(col) if col else (GREEN if i == len(panels) - 1 else WHITE)
            pad = 22
            bh = 60 + pad
            d.rounded_rectangle((36, py + 30, 36 + tw + pad * 2, py + 30 + bh), radius=18, fill=fill)
            d.text((36 + pad, py + 30 + pad // 2 - 2), lab, font=f, fill=NAVY)
    footer(img, o.get("hashtag", "#pracawgamedevie"))
    return img


# ------------------------------------------------------------------ chat
def render_chat(o):
    img = Image.new("RGBA", (W, H), (18, 18, 22, 255))
    d = ImageDraw.Draw(img)
    msgs = o["messages"]
    y = 60
    nf = font(26, "Medium")
    mf = font(38, "Medium")
    bf = font(38, "Bold")
    for i, (who, txt) in enumerate(msgs):
        me = who.strip().lower() in ("ja", "me", "i")
        f = bf if o.get("bold_last") and i == len(msgs) - 1 else mf
        lines = wrap(d, txt, f, 760)
        lh = int(f.size * 1.3)
        bw = max(text_w(d, ln, f) for ln in lines) + 56
        bh = lh * len(lines) + 36
        x = W - 60 - bw if me else 60
        fill = (0, 132, 255) if me else (58, 58, 66)
        d.text((x + 8, y), who, font=nf, fill=(150, 150, 160))
        y += 34
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=28, fill=fill)
        for j, ln in enumerate(lines):
            d.text((x + 28, y + 18 + j * lh), ln, font=f, fill=WHITE)
        y += bh + 18
    y += 20
    if o.get("image"):
        ih = H - y - 86
        pim = load_image(o["image"], W - 120, ih, o.get("fit", "cover"), tuple(o.get("bg", WHITE)), o.get("anchor", 0.4))
        mask = Image.new("L", pim.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, pim.width - 1, pim.height - 1), radius=32, fill=255)
        img.paste(pim, (60, y), mask)
    footer(img, o.get("hashtag", "#pracawgamedevie"))
    return img


RENDERERS = {"scene": render_scene, "panels": render_panels, "chat": render_chat}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    o = json.load(open(a.json, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.json))
    # ścieżki względne w JSON liczone od pliku JSON
    for k in ("image",):
        if o.get(k) and not os.path.isabs(o[k]):
            o[k] = os.path.join(base, o[k])
    for p in o.get("panels", []):
        if not os.path.isabs(p["image"]):
            p["image"] = os.path.join(base, p["image"])
    img = RENDERERS[o.get("mode", "scene")](o)
    img.convert("RGB").save(a.out, optimize=True)
    print("ok", a.out)
