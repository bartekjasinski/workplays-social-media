#!/usr/bin/env python3
"""Memy z pozami maskotki wygenerowanymi w ElevenLabs: jasne tła, zmienne palety i wzory,
treść naklejana na rekwizyt (telefon / zwój / kartka) z perspektywą.
Użycie: python3 pose_memes.py <nazwa: pon|czw|pt> <out.png>
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pose_tools import cutout, put_on_card
from meme_v4 import pop, mono, tw, wrap, fit, vgrad, logo

GEN = os.path.join(os.path.dirname(HERE), "assets", "generated", "2026-11-23")
W, H = 1080, 1350


def quad_of(path, box=None, thr=243):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    m = a.min(2) > thr
    if box:
        x0, y0, x1, y1 = box
        mm = np.zeros_like(m); mm[y0:y1, x0:x1] = m[y0:y1, x0:x1]; m = mm
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    ys, xs = np.where(lab == int(np.argmax(sizes)) + 1)
    s, d = xs + ys, xs - ys
    return [(xs[s.argmin()], ys[s.argmin()]), (xs[d.argmax()], ys[d.argmax()]),
            (xs[s.argmax()], ys[s.argmax()]), (xs[d.argmin()], ys[d.argmin()])]


def caption(img, text, color, y=60, start=60):
    d = ImageDraw.Draw(img)
    s = text.upper()
    f = fit(d, s, 960, start, 40, 3, lambda z: pop(z, "Bold"))
    for ln in wrap(d, s, f, 960):
        d.text(((W - tw(d, ln, f)) // 2, y), ln, font=f, fill=color)
        y += int(f.size * 1.16)
    return y


def pill(img, xy, text, bg, fg, size=28, angle=0):
    d0 = ImageDraw.Draw(img); f = pop(size, "Bold")
    w, h = tw(d0, text, f) + 2 * size, int(size * 1.9)
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0)); td = ImageDraw.Draw(t)
    td.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg)
    td.text((size, int(size * 0.33)), text, font=f, fill=fg)
    if angle:
        t = t.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(t, (int(xy[0]), int(xy[1])))


def place(img, fig, height, cx, bottom):
    fig = fig.crop(fig.getbbox())
    f = fig.resize((round(fig.width * height / fig.height), height), Image.LANCZOS)
    # miękki cień pod postacią
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - f.width * 0.32, H - bottom - 26, cx + f.width * 0.32, H - bottom + 14), fill=(0, 0, 0, 55))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    img.alpha_composite(f, (int(cx - f.width / 2), H - bottom - f.height))
    return img


def footer(img, bg, fg):
    pill(img, (W - 300, H - 92), "workplays.it", bg, fg, 28)


# ------------------------------------------------------------------ PON: lilia + brzoskwinia, wzór kopert
def pon(out):
    src = os.path.join(GEN, "pon-telefon-2.png")
    img = vgrad(W, H, (244, 236, 255), (255, 226, 214))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    rnd = random.Random(7)
    for _ in range(26):
        x, y = rnd.randint(-20, W), rnd.randint(260, H)
        s = rnd.randint(40, 70); c = (150, 110, 220, 38)
        ld.rounded_rectangle((x, y, x + s, y + s * 0.7), radius=6, outline=c, width=4)
        ld.line((x, y, x + s / 2, y + s * 0.38, x + s, y), fill=c, width=4)
    img = Image.alpha_composite(img, lay)
    capy = caption(img, "Kiedy odmowa przyszła szybciej niż potwierdzenie, że CV doszło", (59, 31, 92))
    # ekran telefonu
    q = quad_of(src)
    sw, sh = 600, 1190
    scr = Image.new("RGBA", (sw, sh), (250, 250, 253, 255)); d = ImageDraw.Draw(scr)
    d.text((40, 30), "23:59", font=pop(44, "Bold"), fill=(30, 30, 40))
    d.text((40, 110), "Odebrane", font=pop(64, "Bold"), fill=(59, 31, 92))
    d.rounded_rectangle((20, 230, sw - 20, 640), radius=34, fill=(255, 232, 232))
    d.text((50, 260), "noreply@studio · 23:59", font=pop(34, "Bold"), fill=(220, 50, 50))
    d.text((50, 320), "Niestety…", font=pop(84, "Bold"), fill=(220, 50, 50))
    for i, ln in enumerate(["Zdecydowaliśmy się", "na innych kandydatów."]):
        d.text((50, 440 + i * 56), ln, font=pop(40, "Medium"), fill=(90, 70, 90))
    d.rounded_rectangle((20, 680, sw - 20, 960), radius=34, fill=(238, 236, 246))
    d.text((50, 710), "Ja · 23:58", font=pop(34, "Bold"), fill=(110, 110, 130))
    d.text((50, 770), "Aplikacja:", font=pop(46, "Bold"), fill=(40, 40, 60))
    d.text((50, 830), "Junior Game Designer", font=pop(40, "Medium"), fill=(40, 40, 60))
    fig = put_on_card(cutout(src), q, scr, inset=0.035)
    img = place(img, fig, 960, 650, 40)
    pill(img, (30, capy + 120), "Wysłano: 23:58", (59, 31, 92), (255, 255, 255), 30, 6)
    pill(img, (40, capy + 225), "Odmowa: 23:59", (255, 92, 92), (255, 255, 255), 30, -5)
    pill(img, (24, capy + 330), "Czas czytania CV: 0 s", (255, 196, 61), (59, 31, 92), 26, 4)
    footer(img, (59, 31, 92), (112, 238, 142))
    img.convert("RGB").save(out)


# ------------------------------------------------------------------ CZW: mięta + błękit, siatka kropek
def czw(out):
    src = os.path.join(GEN, "czw-lista-1.png")
    img = vgrad(W, H, (214, 246, 232), (214, 230, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for x in range(20, W, 44):
        for y in range(20, H, 44):
            ld.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(20, 110, 120, 45))
    img = Image.alpha_composite(img, lay)
    capy = caption(img, "Junior 3D Artist: wymagania jak dla całego działu artystycznego", (11, 59, 60), start=56)
    q = quad_of(src, box=(600, 1060, 1150, 2080))
    sw, sh = 420, 1040
    pap = Image.new("RGBA", (sw, sh), (0, 0, 0, 0)); d = ImageDraw.Draw(pap)
    d.text((26, 10), "WYMAGANIA", font=mono(40, True), fill=(11, 59, 60))
    d.text((26, 62), "Junior 3D Artist", font=pop(30, "Medium"), fill=(90, 110, 120))
    items = ["Maya", "Blender", "ZBrush", "Substance", "Houdini", "Unreal + Unity", "Rigging", "Animacja", "VFX i UI", "Photoshop"]
    y = 120
    for it in items:
        d.text((26, y), "☐  " if False else "•  " + it, font=pop(36, "Medium"), fill=(30, 40, 50)); y += 70
    d.text((26, y + 6), "2 gry AAA", font=pop(40, "Bold"), fill=(220, 50, 50))
    d.ellipse((6, y - 4, 300, y + 62), outline=(220, 50, 50), width=6)
    fig = put_on_card(cutout(src), q, pap, inset=0.02)
    img = place(img, fig, 1020, 560, 30)
    pill(img, (40, capy + 100), "POZIOM: 1", (11, 59, 60), (112, 238, 142), 30, -6)
    pill(img, (790, capy + 180), "XP: 0", (154, 132, 255), (255, 255, 255), 30, 7)
    pill(img, (760, 980), "…i ciąg dalszy", (255, 255, 255), (11, 59, 60), 26, -4)
    footer(img, (11, 59, 60), (112, 238, 142))
    img.convert("RGB").save(out)


# ------------------------------------------------------------------ PT: słoneczny żółty + brzoskwinia, promienie
def pt(out):
    src = os.path.join(GEN, "pt-miecz-1.png")
    img = vgrad(W, H, (255, 246, 214), (255, 214, 196))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    cx, cy = 600, 760
    for i in range(24):
        a0 = i * 2 * math.pi / 24; a1 = a0 + math.pi / 24
        ld.polygon([(cx, cy), (cx + 1600 * math.cos(a0), cy + 1600 * math.sin(a0)), (cx + 1600 * math.cos(a1), cy + 1600 * math.sin(a1))], fill=(255, 196, 61, 55))
    img = Image.alpha_composite(img, lay)
    capy = caption(img, "Kiedy w CV piszesz „6 lat zarządzania zespołem”, a chodzi o gildię w MMO", (110, 30, 40), start=56)
    q = quad_of(src, box=(300, 1320, 740, 1700))
    sw, sh = 400, 340
    cv = Image.new("RGBA", (sw, sh), (0, 0, 0, 0)); d = ImageDraw.Draw(cv)
    d.text((30, 4), "CV", font=pop(64, "Bold"), fill=(110, 30, 40))
    d.text((30, 96), "Lider zespołu", font=pop(42, "Bold"), fill=(30, 30, 40))
    d.text((30, 156), "6 lat · 40 osób", font=pop(38, "Medium"), fill=(60, 60, 70))
    d.text((30, 220), "Firma: gildia", font=pop(34, "Regular"), fill=(110, 110, 120))
    d.text((30, 266), "„Smocze Kebaby”", font=pop(34, "Bold"), fill=(220, 50, 50))
    fig = put_on_card(cutout(src), q, cv, inset=0.04)
    img = place(img, fig, 1000, 600, 40)
    pill(img, (40, capy + 110), "+100 do charyzmy", (110, 30, 40), (255, 214, 120), 30, -7)
    pill(img, (820, capy + 560), "HR: ?", (255, 255, 255), (110, 30, 40), 34, 8)
    footer(img, (110, 30, 40), (255, 214, 120))
    img.convert("RGB").save(out)


if __name__ == "__main__":
    {"pon": pon, "czw": czw, "pt": pt}[sys.argv[1]](sys.argv[2])
    print("ok", sys.argv[2])
