#!/usr/bin/env python3
"""WorkPlays – oferta jako „karta przedmiotu” (loot) i pytanie jako „wybór dialogowy” RPG.

Użycie:
  python3 rpg_cards.py --json dane.json --out plik.png [--all-formats]
    --all-formats: dla "loot" zapisuje <plik>_4x5.png, _1x1.png, _9x16.png

JSON:
  {"kind":"loot","label":"OFERTA TYGODNIA","rarity":"LEGENDARNA",
   "title":"Core Tech Programmer","company":"Render Cube","type":"Mid / Senior · Unreal Engine · C++",
   "salary":"10 000 – 25 000 zł","salary_note":"brutto / mies.",
   "perks":["Umowa o pracę","..."],"info":["Łódź · stacjonarnie"],"requirements":["Wymaga: ..."],
   "flavor":"„Start: styczeń 2027”"}
  {"kind":"dialog","speaker":"Pytanie tygodnia","question":"...","options":["...","..."],
   "cta":"A Ty? Napisz numer w komentarzu","mascot":{"image":"../assets/npc1.png","height":700,"x":0.5}}
Maskotka: zawsze oryginalny PNG z assets/ (tylko skalowanie).
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFilter
from meme_v3 import pop, pixel, mono, tw, wrap, glow, shadow, NAVY, GREEN, AMBER, CORAL, VIOLET, WHITE, MUTED, HERE

LOGO = os.path.join(HERE, "logo_alpha.png")


def grad(w, h, c1, c2):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        for x in range(w):
            t = (x / w) * 0.35 + (y / h) * 0.65
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return g.convert("RGBA")


def logo(img, x, y, height=64):
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA")
        lg = lg.resize((round(lg.width * height / lg.height), height), Image.LANCZOS)
        img.alpha_composite(lg, (x, y))


def sparkles(img, seed=3, n=40, color=AMBER):
    import random
    r = random.Random(seed)
    d = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(n):
        x, y, s = r.randint(0, w), r.randint(0, h), r.choice([4, 6, 8])
        d.rectangle((x, y, x + s, y + s), fill=color + (r.randint(60, 160),))


# ------------------------------------------------------------------ loot
def render_loot(o, w=1080, h=1350):
    img = grad(w, h, (40, 26, 90), (8, 12, 30))
    img = glow(img, w // 2, int(h * 0.48), int(min(w, h) * 0.42), AMBER, 70)
    sparkles(img)
    d = ImageDraw.Draw(img)
    logo(img, 60, 50)
    fl = pixel(22)
    lab = o.get("label", "OFERTA TYGODNIA")
    d.text((w - 60 - tw(d, lab, fl), 64), lab, font=fl, fill=GREEN)
    cw = w - 140
    pad = 54
    # treść karty – najpierw policz wysokość
    lines = []  # (font, text, color, gap_after)
    lines.append(("rar", o.get("rarity", "LEGENDARNA") + " OFERTA", AMBER, 18))
    lines.append((pop(64 if w >= 1080 else 56, "Bold"), o["title"], AMBER, 6))
    lines.append((pop(32, "Bold"), o["company"], WHITE, 4))
    lines.append((pop(26, "Medium"), o.get("type", ""), MUTED, 26))
    lines.append(("sep", None, None, 26))
    lines.append((pop(70, "Bold"), o["salary"], GREEN, 0))
    lines.append((pop(26, "Medium"), o.get("salary_note", ""), GREEN, 26))
    for p in o.get("perks", []):
        lines.append((pop(30, "Medium"), "+ " + p, GREEN, 8))
    lines.append(("gap", None, None, 14))
    for p in o.get("info", []):
        lines.append((pop(30, "Medium"), p, WHITE, 8))
    lines.append(("gap", None, None, 14))
    for p in o.get("requirements", []):
        lines.append((pop(28, "Medium"), p, CORAL, 8))
    if o.get("flavor"):
        lines.append(("gap", None, None, 18))
        lines.append((pop(28, "Italic"), o["flavor"], AMBER, 0))
    compact = h <= 1080
    if compact:  # 1:1 – bez części linii
        keep_perks = set(o.get("perks", [])[:1])
        lines = [l for l in lines if l[2] not in (CORAL,) and not (l[2] == AMBER and l[0] not in ("rar",) and l[1] == o.get("flavor"))
                 and not (l[2] == GREEN and str(l[1]).startswith("+ ") and l[1][2:] not in keep_perks)]
        lines = [(l[0], l[1], l[2], min(l[3], 14)) for l in lines]
    def lh(l):
        f, t, c, g = l
        if f == "rar":
            return 44 + g
        if f == "sep":
            return 4 + g
        if f == "gap":
            return g
        n = len(wrap(d, t, f, cw - 2 * pad))
        return n * int(f.size * 1.22) + g
    ch = sum(lh(l) for l in lines) + 2 * pad
    btn_h = 84
    total = ch + 40 + btn_h
    y0 = max(150, (h - total) // 2 + 20)
    x0 = 70
    img = shadow(img, (x0, y0, x0 + cw, y0 + ch), radius=18, off=(0, 20), blur=30, alpha=170)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0, x0 + cw, y0 + ch), radius=18, fill=(14, 16, 30), outline=AMBER, width=4)
    d.rounded_rectangle((x0 + 10, y0 + 10, x0 + cw - 10, y0 + ch - 10), radius=12, outline=(120, 90, 30), width=2)
    y = y0 + pad
    for l in lines:
        f, t, c, g = l
        if f == "rar":
            fr = pixel(20)
            bw = tw(d, t, fr) + 36
            d.rectangle((x0 + pad, y, x0 + pad + bw, y + 40), fill=AMBER)
            d.text((x0 + pad + 18, y + 10), t, font=fr, fill=NAVY)
            y += 44 + g
            continue
        if f == "sep":
            d.line((x0 + pad, y, x0 + cw - pad, y), fill=(120, 90, 30), width=3)
            d.polygon([(w // 2 - 12, y + 1), (w // 2, y - 11), (w // 2 + 12, y + 1), (w // 2, y + 13)], fill=AMBER)
            y += 4 + g
            continue
        if f == "gap":
            y += g
            continue
        for ln in wrap(d, t, f, cw - 2 * pad):
            d.text((x0 + pad, y), ln, font=f, fill=c)
            y += int(f.size * 1.22)
        y += g
    # przycisk
    by = y0 + ch + 40
    fb = pop(34, "Bold")
    bt = "Zbierz loot: workplays.it"
    bw = tw(d, bt, fb) + 80
    bx = x0 if o.get("mascot") else (w - bw) // 2
    d.rounded_rectangle((bx, by, bx + bw, by + btn_h), radius=42, fill=GREEN)
    d.text((bx + 40, by + 18), bt, font=fb, fill=NAVY)
    m = o.get("mascot")
    if m:
        a = Image.open(os.path.join(HERE, m["image"])).convert("RGBA")
        if m.get("flip"):
            a = a.transpose(Image.FLIP_LEFT_RIGHT)
        mh = int(min(m.get("height", 460), h * 0.36))
        a = a.resize((round(a.width * mh / a.height), mh), Image.LANCZOS)
        img.alpha_composite(a, (w - a.width - 30, min(h - mh - 10, by + btn_h + 40 - mh // 2 if h > 1400 else h - mh - 10)))
    return img


# ------------------------------------------------------------------ dialog
def render_dialog(o, w=1080, h=1350):
    img = grad(w, h, (255, 150, 105), (110, 90, 230))
    img = glow(img, int(w * 0.5), 380, 300, (255, 230, 150), 110)
    d = ImageDraw.Draw(img)
    logo(img, 60, 50)
    # maskotka nad oknem dialogowym
    m = o["mascot"]
    a = Image.open(os.path.join(HERE, m["image"])).convert("RGBA")
    mh = int(m.get("height", 640))
    a = a.resize((round(a.width * mh / a.height), mh), Image.LANCZOS)
    box_top = int(h * 0.50)
    img.alpha_composite(a, (int(w * m.get("x", 0.5) - a.width / 2), box_top + 120 - mh))
    # okno dialogowe
    bx0, bx1, by1 = 40, w - 40, h - 40
    img = shadow(img, (bx0, box_top, bx1, by1), radius=24, off=(0, 16), blur=24, alpha=150)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle((bx0, box_top, bx1, by1), radius=24, fill=(10, 14, 32, 238), outline=WHITE + (255,), width=4)
    img = Image.alpha_composite(img, lay)
    d = ImageDraw.Draw(img)
    # tabliczka z imieniem
    fs = pixel(22)
    sp = o.get("speaker", "PYTANIE TYGODNIA").upper()
    sw = tw(d, sp, fs) + 44
    d.rounded_rectangle((bx0 + 40, box_top - 30, bx0 + 40 + sw, box_top + 30), radius=10, fill=AMBER)
    d.text((bx0 + 62, box_top - 10), sp, font=fs, fill=NAVY)
    fq = pop(48, "Bold")
    y = box_top + 60
    for ln in wrap(d, o["question"], fq, bx1 - bx0 - 100):
        d.text((bx0 + 50, y), ln, font=fq, fill=WHITE)
        y += 60
    y += 30
    fo = pop(38, "Medium")
    cols = [GREEN, AMBER, CORAL, VIOLET]
    for i, op in enumerate(o["options"]):
        num = f"[{i + 1}]"
        fn = pixel(24)
        if i == 0:
            d.polygon([(bx0 + 30, y + 12), (bx0 + 46, y + 24), (bx0 + 30, y + 36)], fill=WHITE)
        d.text((bx0 + 56, y + 10), num, font=fn, fill=cols[i % 4])
        d.text((bx0 + 56 + tw(d, num, fn) + 22, y), op, font=fo, fill=WHITE)
        y += 72
    fc = pop(30, "Bold")
    cta = o.get("cta", "A Ty? Napisz numer w komentarzu")
    d.text((bx0 + 50, by1 - 70), cta, font=fc, fill=GREEN)
    fw = pop(26, "Bold")
    d.text((bx1 - 50 - tw(d, "workplays.it", fw), by1 - 66), "workplays.it", font=fw, fill=MUTED)
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--all-formats", action="store_true")
    a = ap.parse_args()
    o = json.load(open(a.json, encoding="utf-8"))
    fn = {"loot": render_loot, "dialog": render_dialog}[o["kind"]]
    if a.all_formats:
        base = a.out[:-4] if a.out.endswith(".png") else a.out
        for tag, (w, h) in {"4x5": (1080, 1350), "1x1": (1080, 1080), "9x16": (1080, 1920)}.items():
            fn(o, w, h).convert("RGB").save(f"{base}_{tag}.png")
            print("ok", f"{base}_{tag}.png")
    else:
        fn(o).convert("RGB").save(a.out)
        print("ok", a.out)
