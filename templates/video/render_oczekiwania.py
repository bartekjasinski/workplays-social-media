"""WorkPlays TikTok – odcinek C „Pytają o oczekiwania finansowe”.
Plansza z tipami (granatowy gradient) + popiersie maskotki w prawym dolnym rogu.
Użycie: python3 render_c.py out_silent.mp4 [podgląd_t1 t2 ...]
Maskotka: oryginalny programista_100.png (bez zmian), lekko „oddycha”/podskakuje w rytm lektora.
Jeśli istnieje mascot.mp4 (OmniHuman, 960x960 na zielonym) – użyj trybu --omni mascot.mp4.
"""
import math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = "/home/claude/workplays-social-media"
W, H, FPS = 1080, 1920, 30
END = 23.6
LIME = (112, 238, 142); WHITE = (245, 245, 245); GREY = (150, 160, 180); RED = (255, 92, 92)
DARK = (14, 20, 40); AMBER = (255, 196, 61); VIOLET = (154, 132, 255)
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
_fc = {}
def F(p, s):
    k = (p, max(1, int(s)))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, k[1])
    return _fc[k]
def cl(x): return max(0.0, min(1.0, x))
def eo(t): t = cl(t); return 1 - (1 - t) ** 3
def back(t):
    t = cl(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t

# ---- timings (Scribe, take 1) ----
T = dict(hook=0.13, bubble=2.76, blad=5.34,
         one=6.30, spr=7.34,
         two=9.60, przedz=9.82, dol=10.80, mini=12.30,
         three=13.95, brutto=15.09, netto=16.0, umowa=16.59, b2b=17.76,
         cta=18.68)
SCENES = [("hook", 0.0), ("one", T["one"]), ("two", T["two"]), ("three", T["three"]), ("cta", T["cta"]), ("end", 99)]

logo = Image.open(f"{REPO}/templates/logo_alpha.png").convert("RGBA")

GRAD = Image.new("RGB", (1, H))
for y in range(H):
    k = y / H; GRAD.putpixel((0, y), (int(lerp(12, 6, k)), int(lerp(20, 10, k)), int(lerp(44, 22, k))))
GRAD = GRAD.resize((W, H)).convert("RGBA")
def bg(t):
    s = 8; g = Image.new("RGBA", (W // s, H // s), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    cx = (W * 0.3 + 260 * math.sin(t * 0.3)) / s; cy = (H * 0.28 + 200 * math.cos(t * 0.25)) / s
    d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(40, 90, 230, 70))
    cx2 = (W * 0.75 - 200 * math.sin(t * 0.27 + 1)) / s; cy2 = (H * 0.8 + 120 * math.sin(t * 0.2)) / s
    d.ellipse([cx2 - 55, cy2 - 55, cx2 + 55, cy2 + 55], fill=(90, 60, 200, 50))
    g = g.filter(ImageFilter.GaussianBlur(20)).resize((W, H), Image.BILINEAR)
    f = GRAD.copy(); f.alpha_composite(g); return f

def txt(d, xy, s, f, fill=WHITE, a=1.0, anchor="la"):
    if a <= 0: return
    d.text(xy, s, font=f, fill=fill + (int(255 * cl(a)),), anchor=anchor)
def pill(d, cx, cy, s, f, a=1.0, bgc=LIME, fg=DARK, padx=34, pady=18):
    if a <= 0: return 0
    tw = d.textlength(s, font=f); w, h = tw + 2 * padx, f.size + 2 * pady
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], h / 2, fill=bgc + (int(255 * cl(a)),))
    d.text((cx, cy + 2), s, font=f, fill=fg + (int(255 * cl(a)),), anchor="mm"); return w
def check(d, x, y, sz, a=1.0, col=LIME):
    if a <= 0: return
    d.ellipse([x, y, x + sz, y + sz], fill=col + (int(255 * a),))
    d.line([(x + sz * .27, y + sz * .52), (x + sz * .45, y + sz * .7), (x + sz * .75, y + sz * .32)],
           fill=DARK + (int(255 * a),), width=max(3, int(sz * .12)), joint="curve")
def header(d, num, title, lt, y=330):
    for i in range(3):
        on = i < num; x = W / 2 - 90 + i * 90
        d.rounded_rectangle([x - 34, 150, x + 34, 166], 8, fill=(LIME if on else (60, 70, 100)) + (255,))
    k = back(lt / 0.45); a = cl(lt / 0.2); r = 80 * k
    d.ellipse([140 - r, y - r, 140 + r, y + r], fill=LIME + (int(255 * a),))
    txt(d, (140, y + 4), str(num), F(FB, 110 * max(k, .01)), DARK, a, "mm")
    x0 = 250 + 60 * (1 - eo((lt - 0.08) / 0.35))
    txt(d, (x0, y + 6), title, F(FB, 92), WHITE, (lt - 0.08) / 0.25, "lm")

# ---- scenes ----
def s_hook(d, t):
    lt = t - T["hook"]; k = back(lt / 0.4); a = cl(lt / 0.15)
    txt(d, (W / 2, 300), "PYTAJĄ O", F(FB, 118 * (1.25 - 0.25 * k)), WHITE, a, "mm")
    l2 = lt - 0.5; sh = 6 * math.sin(l2 * 60) * max(0, 1 - l2 / 0.35) if l2 > 0 else 0
    for i, ln in enumerate(["OCZEKIWANIA", "FINANSOWE?"]):
        li = l2 - i * 0.18; s2 = back(li / 0.35)
        txt(d, (W / 2 + sh, 440 + i * 125), ln, F(FB, 108 * (1.2 - 0.2 * s2)), LIME, li / 0.15, "mm")
    # chat bubble: "Ile państwo proponują?"
    lb = t - T["bubble"]
    if lb > -0.1:
        a = cl(lb / 0.25); y0 = 690 + 40 * (1 - eo(lb / 0.35))
        d.rounded_rectangle([120, y0, W - 120, y0 + 190], 44, fill=(255, 255, 255, int(28 * a)), outline=(255, 255, 255, int(90 * a)), width=3)
        d.polygon([(190, y0 + 190), (240, y0 + 190), (180, y0 + 240)], fill=(255, 255, 255, int(28 * a)))
        txt(d, (170, y0 + 32), "Ty:", F(FM, 38), GREY, a)
        full = "„Ile państwo proponują?”"; n = int(len(full) * cl((lb - 0.05) / 1.0)); s = full[:n]
        txt(d, (170, y0 + 82), s, F(FB, 62), WHITE, a)
    # BŁĄD! stamp
    lz = t - T["blad"]
    if lz > 0:
        k = back(lz / 0.3); a = cl(lz / 0.1); sh = 8 * math.sin(lz * 70) * max(0, 1 - lz / 0.4)
        f = F(FB, 150 * (1.6 - 0.6 * k))
        f = F(FB, 130 * (1.6 - 0.6 * k))
        lay = Image.new("RGBA", (600, 260), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle([20, 35, 580, 225], 28, outline=RED + (int(255 * a),), width=11)
        ld.text((300, 132), "BŁĄD!", font=f, fill=RED + (int(255 * a),), anchor="mm")
        lay = lay.rotate(-7, resample=Image.BICUBIC, expand=False)
        d._image.alpha_composite(lay, (int(110 + sh), 925))

OFFERS = [("Unity Developer", "9 000 – 13 000 zł"), ("Gameplay Developer", "12 000 – 17 000 zł"), ("Tools Programmer", "11 000 – 16 000 zł")]
def s_one(d, t):
    lt = t - T["one"]; header(d, 1, "SPRAWDŹ", lt)
    txt(d, (110, 470 + 20 * (1 - eo(lt / .3))), "widełki w podobnych ofertach", F(FB, 56), LIME, lt / .25)
    l2 = t - T["spr"]
    for i, (role, rng) in enumerate(OFFERS):
        li = l2 - i * 0.3
        if li < 0: continue
        a = cl(li / .2); y = 600 + i * 150 + 30 * (1 - eo(li / .3))
        d.rounded_rectangle([110, y, W - 110, y + 120], 30, fill=(255, 255, 255, int(22 * a)), outline=(255, 255, 255, int(60 * a)), width=2)
        txt(d, (150, y + 60), role, F(FM, 40), WHITE, a, "lm")
        pill(d, W - 110 - 24 - d.textlength(rng, font=F(FB, 34)) / 2 - 22, y + 60, rng, F(FB, 34), a, padx=22, pady=12)
    l3 = l2 - 1.3
    if l3 > 0:
        txt(d, (W / 2, 1110 + 20 * (1 - eo(l3 / .3))), "= realny przedział na rynku", F(FM, 46), GREY, l3 / .25, "mm")

def s_two(d, t):
    lt = t - T["two"]; header(d, 2, "PODAJ PRZEDZIAŁ", lt)
    l1 = t - T["przedz"]
    # range bar
    x1, x2, yb = 140, W - 140, 760
    if l1 > 0:
        a = cl(l1 / .25)
        d.rounded_rectangle([x1, yb - 14, x2, yb + 14], 14, fill=(60, 70, 100, int(255 * a)))
        k = eo(l1 / .6); xa, xb = lerp(W / 2, 330, k), lerp(W / 2, 880, k)
        d.rounded_rectangle([xa, yb - 22, xb, yb + 22], 22, fill=LIME + (int(255 * a),))
        txt(d, (W / 2, 620), "12 000 – 15 000 zł", F(FB, 84), WHITE, (l1 - .2) / .25, "mm")
    l2 = t - T["dol"]
    if l2 > 0:
        a = cl(l2 / .25); xm = 250
        # minimum marker
        d.line([(xm, yb - 60), (xm, yb + 60)], fill=AMBER + (int(255 * a),), width=6)
        txt(d, (xm, yb + 110), "Twoje minimum", F(FM, 36), AMBER, a, "mm")
        txt(d, (xm, yb + 155), "11 000 zł", F(FB, 40), AMBER, a, "mm")
        # arrow from minimum to bottom of range
        k = eo((l2 - .3) / .5)
        if k > 0:
            xe = lerp(xm + 10, 320, k)
            d.line([(xm + 10, yb - 90), (xe, yb - 90)], fill=LIME + (int(255 * a),), width=6)
            d.polygon([(xe + 16, yb - 90), (xe - 4, yb - 102), (xe - 4, yb - 78)], fill=LIME + (int(255 * a * k),))
    l3 = t - T["mini"]
    if l3 > 0:
        pill(d, W / 2, 1080 + 25 * (1 - eo(l3 / .3)), "dół trochę wyżej niż minimum", F(FB, 52), l3 / .2)

ROWS = [("BRUTTO", "NETTO", "brutto", "netto"), ("UoP", "B2B", "umowa", "b2b")]
def s_three(d, t):
    lt = t - T["three"]; header(d, 3, "ZAWSZE DOPYTAJ", lt)
    for i, (l, r, tl, tr) in enumerate(ROWS):
        y = 560 + i * 260
        la, ra = t - T[tl], t - T[tr]
        if la > -0.05:
            a = cl(la / .2); dy = 30 * (1 - eo(la / .3))
            pill(d, 300, y + dy, l, F(FB, 70), a, bgc=(255, 255, 255), fg=DARK, padx=46, pady=24)
            txt(d, (W / 2, y + dy + 4), "czy", F(FM, 48), GREY, a, "mm")
        if ra > -0.05:
            a = cl(ra / .2); dy = 30 * (1 - eo(ra / .3))
            pill(d, W - 300, y + dy, r, F(FB, 70), a, bgc=(255, 255, 255), fg=DARK, padx=46, pady=24)
            check(d, W - 140, y - 70, 56, cl((ra - .3) / .2))
    l3 = t - T["b2b"] - 0.35
    if l3 > 0:
        txt(d, (W / 2, 1080 + 20 * (1 - eo(l3 / .3))), "Te same widełki to różne pieniądze.", F(FM, 46), LIME, l3 / .25, "mm")

def s_cta(d, t, frame):
    lt = t - T["cta"]; k = back(lt / .45); a = cl(lt / .2)
    lw = int(560 * max(k, .05)); lg = logo.resize((lw, max(1, int(logo.height * lw / logo.width))), Image.LANCZOS)
    lg.putalpha(lg.split()[3].point(lambda v: int(v * a)))
    frame.alpha_composite(lg, (int(W / 2 - lw / 2), int(420 - lg.height / 2)))
    txt(d, (W / 2, 600), "workplays.it", F(FB, 120), LIME, (lt - .2) / .2, "mm")
    l4 = lt - .55
    txt(d, (W / 2, 715 + 25 * (1 - eo(l4 / .3))), "Praca w gamedevie", F(FM, 58), WHITE, l4 / .25, "mm")
    txt(d, (W / 2, 790 + 25 * (1 - eo(l4 / .3))), "oferty z widełkami", F(FM, 44), GREY, l4 / .25, "mm")
    l3 = lt - .9; bob = 6 * math.sin(lt * 6) if l3 > .4 else 0
    pill(d, W / 2, 920 + bob + 30 * (1 - eo(l3 / .3)), "Daj się znaleźć  >", F(FB, 60), l3 / .2, padx=50, pady=26)

DRAW = dict(hook=s_hook, one=s_one, two=s_two, three=s_three)
OFF = 200
def board(t, frame):
    for i in range(len(SCENES) - 1):
        name, st = SCENES[i]; nxt = SCENES[i + 1][1]
        if st <= t < nxt:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
            if name == "cta": s_cta(d, t, layer)
            else: DRAW[name](d, t)
            out = cl((nxt - t) / 0.18); dy = int(-40 * (1 - out))
            if out < 1: layer.putalpha(layer.split()[3].point(lambda v: int(v * out)))
            frame.alpha_composite(layer, (0, dy + OFF))

# ---- mascot ----
BUST, BH = 600, 550
BX, BY = W - BUST + 30, H - BH
GLOW = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(GLOW).ellipse([BX + 90, BY + 60, BX + BUST - 90, BY + BUST + 120], fill=(80, 130, 255, 70))
GLOW = GLOW.filter(ImageFilter.GaussianBlur(60))
src = Image.open(f"{REPO}/assets/programista_100.png").convert("RGBA")
src = src.crop(src.getbbox()).crop((0, 0, 599, 930))  # głowa + ramiona, bez dłoni
MS = src.resize((int(src.width * BH / src.height * 1.0), BH), Image.LANCZOS)

def env():
    w = wave.open("/tmp/claude-0/vid/take1_low.wav"); n = w.getnframes(); sr = w.getframerate(); ch = w.getnchannels()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32).reshape(-1, ch).mean(1) / 32768
    hop = sr // FPS; e = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n // hop)])
    e = e / (e.max() + 1e-9); sm = np.convolve(e, np.ones(3) / 3, mode="same"); return sm
ENV = env()

def mascot(fr, t, i):
    e = ENV[i] if i < len(ENV) else 0.0
    ent = eo(t / 0.35)
    bob = -10 * e + 4 * math.sin(t * 2.2)
    tilt = 2.0 * math.sin(t * 1.3) + 1.5 * e * math.sin(t * 9)
    m = MS.rotate(tilt, resample=Image.BICUBIC, center=(MS.width / 2, MS.height), expand=False)
    x = BX + (BUST - m.width) // 2
    fr.alpha_composite(m, (x, int(BY + bob + (1 - ent) * 200)))

def main():
    out = sys.argv[1]; previews = [float(x) for x in sys.argv[2:]]
    enc = None
    if not previews:
        enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(int(END * FPS)):
        t = i / FPS
        if previews and not any(abs(t - p) < 0.5 / FPS for p in previews): continue
        fr = bg(t); board(t, fr); fr.alpha_composite(GLOW); mascot(fr, t, i)
        if previews: fr.convert("RGB").save(f"/tmp/claude-0/vid/prev_{t:05.2f}.jpg", quality=85)
        else: enc.stdin.write(fr.tobytes())
    if enc: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    main()
