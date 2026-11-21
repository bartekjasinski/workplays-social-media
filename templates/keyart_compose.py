#!/usr/bin/env python3
"""Składanie key artu (pełna ilustrowana scena z ElevenLabs) w post 1080x1350:
podpis u góry, treść na ekranie rekwizytu, pływająca karta-powiadomienie, workplays.it."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pose_tools import put_on_card
from meme_v4 import pop, tw, wrap, fit

W, H = 1080, 1350


def screen_quad(a, thr=235):
    m = a.min(2) > thr
    lab, n = ndimage.label(m); s = ndimage.sum(m, lab, range(1, n + 1))
    ys, xs = np.where(lab == int(np.argmax(s)) + 1)
    sm, df = xs + ys, xs - ys
    return [(xs[sm.argmin()], ys[sm.argmin()]), (xs[df.argmax()], ys[df.argmax()]),
            (xs[sm.argmax()], ys[sm.argmax()]), (xs[df.argmin()], ys[df.argmin()])]


def main(src, out):
    im = Image.open(src).convert("RGBA")
    sc = H / im.height
    im = im.resize((round(im.width * sc), H), Image.LANCZOS)
    off = (im.width - W) // 2
    im = im.crop((off, 0, off + W, H))
    a = np.asarray(im.convert("RGB")).astype(int)
    q = screen_quad(a)
    # ekran telefonu
    sw, sh = 300, 600
    scr = Image.new("RGBA", (sw, sh), (0, 0, 0, 0)); d = ImageDraw.Draw(scr)
    d.text((22, 40), "23:59", font=pop(40, "Bold"), fill=(40, 40, 60))
    d.rounded_rectangle((12, 130, sw - 12, 420), radius=26, fill=(255, 232, 232))
    d.text((30, 150), "noreply@studio", font=pop(26, "Bold"), fill=(220, 50, 50))
    d.text((30, 200), "Niestety…", font=pop(46, "Bold"), fill=(220, 50, 50))
    d.text((30, 280), "Zdecydowaliśmy", font=pop(28, "Medium"), fill=(90, 70, 90))
    d.text((30, 318), "się na innych…", font=pop(28, "Medium"), fill=(90, 70, 90))
    im = put_on_card(im, q, scr, inset=0.09)
    # przyciemnienie u góry pod podpis
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(380):
        gd.line((0, y, W, y), fill=(6, 10, 30, int(170 * (1 - y / 380))))
    im = Image.alpha_composite(im, g)
    d = ImageDraw.Draw(im)
    cap = "KIEDY ODMOWA PRZYSZŁA SZYBCIEJ NIŻ POTWIERDZENIE, ŻE CV DOSZŁO"
    f = fit(d, cap, 960, 58, 40, 3, lambda z: pop(z, "Bold"))
    y = 58
    for ln in wrap(d, cap, f, 960):
        x = (W - tw(d, ln, f)) // 2
        d.text((x, y), ln, font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(10, 14, 40))
        y += int(f.size * 1.18)
    # pływające powiadomienie (powiększenie ekranu)
    tx, ty, twd, th = 60, 470, 470, 210
    sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rounded_rectangle((tx + 6, ty + 14, tx + twd + 6, ty + th + 14), radius=26, fill=(0, 0, 0, 140))
    im = Image.alpha_composite(im, sh_.filter(ImageFilter.GaussianBlur(14)))
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle((tx, ty, tx + twd, ty + th), radius=26, fill=(250, 250, 253, 245))
    cd.ellipse((tx + 26, ty + 28, tx + 92, ty + 94), fill=(255, 92, 92))
    cd.text((tx + 46, ty + 36), "S", font=pop(36, "Bold"), fill=(255, 255, 255))
    cd.text((tx + 112, ty + 26), "noreply@studio", font=pop(28, "Bold"), fill=(30, 30, 50))
    cd.text((tx + twd - 26 - tw(cd, "23:59", pop(26, "Bold")), ty + 30), "23:59", font=pop(26, "Bold"), fill=(220, 50, 50))
    cd.text((tx + 112, ty + 66), "Niestety…", font=pop(40, "Bold"), fill=(220, 50, 50))
    cd.text((tx + 26, ty + 132), "Twoja aplikacja wysłana o 23:58.", font=pop(25, "Medium"), fill=(110, 110, 130))
    cd.text((tx + 26, ty + 166), "Potwierdzenie otrzymania: brak", font=pop(25, "Medium"), fill=(110, 110, 130))
    im = Image.alpha_composite(im, card)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((W - 300, H - 86, W - 40, H - 36), radius=25, fill=(10, 14, 40, 230))
    d.text((W - 274, H - 79), "workplays.it", font=pop(28, "Bold"), fill=(112, 238, 142))
    im.convert("RGB").save(out, optimize=True)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
