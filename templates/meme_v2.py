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


# ------------------------------------------------------------------ classic (styl WorkPlays v1, bez przerabiania postaci)
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def emoji_img(ch, size):
    """Renderuje emoji (Noto Color Emoji ma stały rozmiar 109 px, więc skalujemy)."""
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 8), ch, font=f, embedded_color=True)
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    r = size / max(im.size)
    return im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)


def render_classic(o):
    """Ciemne tło, caption u góry (Poppins, biały, zielone wyróżnienia w {nawiasach}),
    biała karta z zieloną obwódką, w niej 1–2 ORYGINALNE assety + opcjonalne emoji-rekwizyty.
    JSON: {"mode":"classic","caption":"Kiedy ... {workplays.it}","chars":[{"image":"...png","scale":1.0,"x":0.5,"flip":false}],
           "props":[{"emoji":"☕","size":140,"x":0.72,"y":0.78}], "caption2": "...", "card_bg":[250,250,250]}"""
    img = Image.new("RGBA", (W, H), (18, 18, 20, 255))
    d = ImageDraw.Draw(img)
    # caption – jak w memach v1: zwykły biały Poppins, fragmenty w {} na zielono
    f = font(50, "Medium")
    raw = o["caption"]
    tokens = []
    for part in raw.replace("}", "{").split("{"):
        tokens.append(part)
    # proste łamanie z kolorowaniem
    x, y, lh = 60, 60, 66
    green = False
    for ti, part in enumerate(tokens):
        for word in part.split(" "):
            if not word:
                continue
            ww = text_w(d, word + " ", f)
            if x + ww > W - 60:
                x, y = 60, y + lh
            d.text((x, y), word, font=f, fill=GREEN if green else WHITE)
            x += ww
        green = not green
    y += lh
    if o.get("caption2"):
        y += 30
        x = 60
        for word in o["caption2"].split(" "):
            ww = text_w(d, word + " ", f)
            if x + ww > W - 60:
                x, y = 60, y + lh
            d.text((x, y), word, font=f, fill=WHITE)
            x += ww
        y += lh
    # karta
    cy0 = max(y + 50, 380)
    cy1 = H - 110
    card = Image.new("RGBA", (W - 2 * 50, cy1 - cy0), tuple(o.get("card_bg", [250, 250, 250])) + (255,))
    cd = ImageDraw.Draw(card)
    chars = o.get("chars", [])
    n = len(chars)
    for i, c in enumerate(chars):
        a = Image.open(c["image"]).convert("RGBA")
        if c.get("flip"):
            a = a.transpose(Image.FLIP_LEFT_RIGHT)
        target_h = int((card.height - 20) * c.get("scale", 1.0))
        r = target_h / a.height
        a = a.resize((round(a.width * r), target_h), Image.LANCZOS)
        cx = c.get("x", (i + 0.5) / n)
        px = int(card.width * cx - a.width / 2)
        py = card.height - a.height + int(c.get("dy", 0))
        card.alpha_composite(a, (px, py))
    for p in o.get("props", []):
        e = emoji_img(p["emoji"], p.get("size", 140))
        card.alpha_composite(e, (int(card.width * p["x"] - e.width / 2), int(card.height * p["y"] - e.height / 2)))
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card.width - 1, card.height - 1), radius=40, fill=255)
    img.paste(card, (50, cy0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((50, cy0, W - 50, cy1), radius=40, outline=GREEN, width=4)
    # stopka jak v1
    logo = Image.open(LOGO).convert("RGBA")
    lh2 = 56
    logo = logo.resize((int(logo.width * lh2 / logo.height), lh2), Image.LANCZOS)
    img.alpha_composite(logo, (50, H - 90))
    hf = font(30, "Medium")
    tag = o.get("hashtag", "#pracawgamedevie")
    d.text((W - 50 - text_w(d, tag, hf), H - 80), tag, font=hf, fill=WHITE)
    return img


RENDERERS["classic"] = render_classic



# ------------------------------------------------------------------ ui (sprawdzona formuła: wersalikowy caption + rekwizyt-UI + oryginalna maskotka)
def _grad(top=(20, 32, 70), bottom=(8, 12, 30)):
    img = Image.new("RGB", (W, H), top)
    px = img.load()
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img.convert("RGBA")


def _card_lines(d, x, y, lines, width):
    """lines: list of dicts {text, style: title|sub|chip|bullet|bullet_red|small}"""
    for ln in lines:
        st = ln.get("style", "bullet")
        if st == "title":
            f = font(44, "Bold"); d.text((x, y), ln["text"], font=f, fill=(20, 24, 40)); y += 58
        elif st == "sub":
            f = font(26, "Medium"); d.text((x, y), ln["text"], font=f, fill=(110, 118, 140)); y += 40
        elif st == "chips":
            cx = x
            for ch in ln["chips"]:
                f = font(24, "Medium")
                tw = text_w(d, ch["text"], f)
                fill = GREEN if ch.get("green") else (236, 239, 246)
                d.rounded_rectangle((cx, y, cx + tw + 36, y + 46), radius=12, fill=fill)
                d.text((cx + 18, y + 9), ch["text"], font=f, fill=(20, 24, 40))
                cx += tw + 36 + 14
            y += 66
        elif st == "head":
            f = font(30, "Bold"); d.text((x, y), ln["text"], font=f, fill=(20, 24, 40)); y += 46
        elif st in ("bullet", "bullet_red"):
            f = font(27, "Regular")
            txt = "•  " + ln["text"]
            lines2 = wrap(d, txt, f, width - 20)
            y0 = y
            for l2 in lines2:
                d.text((x, y), l2, font=f, fill=(30, 34, 50)); y += 38
            if st == "bullet_red":
                tw = max(text_w(d, l2, f) for l2 in lines2)
                d.ellipse((x - 14, y0 - 10, x + min(tw, width - 20) + 14, y + 4), outline=(228, 48, 48), width=5)
            y += 4
        elif st == "small":
            f = font(22, "Regular"); d.text((x, y), ln["text"], font=f, fill=(140, 146, 165)); y += 32
    return y


def render_ui(o):
    img = _grad()
    d = ImageDraw.Draw(img)
    # caption – wersaliki, bold, wyśrodkowany
    cap = o["caption"].upper()
    f = fit(d, cap, W - 100, 60, 40, 4, lambda s: font(s, "Bold"))
    y = 64
    for ln in wrap(d, cap, f, W - 100):
        d.text(((W - text_w(d, ln, f)) // 2, y), ln, font=f, fill=WHITE)
        y += int(f.size * 1.2)
    y += 40
    # rekwizyt: karta UI
    card = o.get("card")
    if card:
        cw = card.get("width", 780)
        cx = card.get("x", 70)
        pad = 40
        # zmierz wysokość
        tmp = Image.new("RGBA", (cw, 1200)); td = ImageDraw.Draw(tmp)
        ch = _card_lines(td, pad, pad, card["lines"], cw - 2 * pad) + pad
        box = Image.new("RGBA", (cw, ch), (250, 250, 252, 255))
        bd = ImageDraw.Draw(box)
        if card.get("notification"):
            # awatar z literą po lewej
            bd.ellipse((pad, pad, pad + 70, pad + 70), fill=GREEN)
            bd.text((pad + 22, pad + 14), card["notification"], font=font(36, "Bold"), fill=(20, 24, 40))
            _card_lines(bd, pad + 95, pad + 2, card["lines"], cw - 2 * pad - 95)
        else:
            _card_lines(bd, pad, pad, card["lines"], cw - 2 * pad)
        mask = Image.new("L", box.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=28, fill=255)
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((cx + 8, y + 16, cx + cw + 8, y + ch + 16), radius=28, fill=(0, 0, 0, 120))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18)))
        img.paste(box, (cx, y), mask)
        card_bottom = y + ch
    else:
        card_bottom = y
    # maskotka – oryginalny asset
    m = o["mascot"]
    a = Image.open(m["image"]).convert("RGBA")
    if m.get("flip"):
        a = a.transpose(Image.FLIP_LEFT_RIGHT)
    mh = int(m.get("height", 620))
    a = a.resize((round(a.width * mh / a.height), mh), Image.LANCZOS)
    mx = int(W * m.get("x", 0.78) - a.width / 2)
    my = H - a.height - m.get("bottom", 70)
    img.alpha_composite(a, (mx, my))
    d = ImageDraw.Draw(img)
    # pasek debug na dole (opcjonalnie)
    if o.get("debug"):
        d.rectangle((0, H - 70, W, H), fill=(14, 16, 24))
        f1 = font(28, "Bold"); f2 = font(28, "Regular")
        d.text((40, H - 52), "[Debug]:", font=f1, fill=(255, 92, 92))
        d.text((40 + text_w(d, "[Debug]: ", f1), H - 52), o["debug"], font=f2, fill=WHITE)
    # workplays.it
    f = font(26, "SemiBold")
    d.text((W - 50 - text_w(d, "workplays.it", f), H - (108 if o.get("debug") else 48)), "workplays.it", font=f, fill=GREEN)
    return img


RENDERERS["ui"] = render_ui


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
    if o.get("mascot") and not os.path.isabs(o["mascot"]["image"]):
        o["mascot"]["image"] = os.path.join(base, o["mascot"]["image"])
    for p in o.get("panels", []) + o.get("chars", []):
        if not os.path.isabs(p["image"]):
            p["image"] = os.path.join(base, p["image"])
    img = RENDERERS[o.get("mode", "scene")](o)
    img.convert("RGB").save(a.out, optimize=True)
    print("ok", a.out)
