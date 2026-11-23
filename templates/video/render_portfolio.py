"""WorkPlays TikTok – odcinek „Portfolio na jedno spojrzenie” (na bazie render_pilot.py)."""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

LOGO_PATH = "/home/claude/workplays-social-media/templates/logo_alpha.png"
W, H, FPS = 1080, 1920, 30
END = 29.3
LIME = (112, 238, 142); WHITE = (245, 245, 245); GREY = (150, 160, 180); RED = (255, 92, 92)
DARK = (14, 20, 40); AMBER = (255, 196, 61)
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
_fc = {}
def F(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]
def cl(x): return max(0.0, min(1.0, x))
def eo(t): t = cl(t); return 1 - (1 - t) ** 3
def back(t):
    t = cl(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t

T = dict(hook=0.12, hook2=1.17, nie=2.12, dzies=3.0,
         raz=6.47, top=7.28, gora=9.2,
         dwa=11.19, zdanie=12.5, ty=13.39,
         trzy=15.9, gif=16.64, wideo=17.88, zamiast=18.84,
         link=21.11, cv=22.0, pdf=22.8,
         cta=25.67)
SCENES = [("hook", 0.0), ("raz", T["raz"]), ("dwa", T["dwa"]), ("trzy", T["trzy"]),
          ("link", T["link"]), ("cta", T["cta"]), ("end", 99)]

logo = Image.open(LOGO_PATH).convert("RGBA")

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
    d.text(xy, s, font=f, fill=fill + (int(255 * cl(a)),), anchor=anchor)
def pill(d, cx, cy, s, f, a=1.0, bgc=LIME, fg=DARK, padx=34, pady=18):
    tw = d.textlength(s, font=f); w, h = tw + 2 * padx, f.size + 2 * pady
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], h / 2, fill=bgc + (int(255 * cl(a)),))
    d.text((cx, cy + 2), s, font=f, fill=fg + (int(255 * cl(a)),), anchor="mm")
    return w
def check(d, x, y, sz, a=1.0, col=LIME):
    d.ellipse([x, y, x + sz, y + sz], fill=col + (int(255 * a),))
    d.line([(x + sz * .27, y + sz * .52), (x + sz * .45, y + sz * .7), (x + sz * .75, y + sz * .32)], fill=DARK + (int(255 * a),), width=max(3, int(sz * .12)), joint="curve")
def strike(d, x1, x2, y, k):
    if k > 0: d.line([(x1, y), (lerp(x1, x2, cl(k)), y)], fill=RED + (255,), width=7)
def header(d, num, title, lt, y=330):
    for i in range(3):
        on = i < num; x = W / 2 - 90 + i * 90
        d.rounded_rectangle([x - 34, 150, x + 34, 166], 8, fill=(LIME if on else (60, 70, 100)) + (255,))
    k = back(lt / 0.45); a = cl(lt / 0.2); r = 80 * k
    d.ellipse([140 - r, y - r, 140 + r, y + r], fill=LIME + (int(255 * a),))
    txt(d, (140, y + 4), str(num), F(FB, int(110 * max(k, .01))), DARK, a, "mm")
    x0 = 250 + 60 * (1 - eo((lt - 0.08) / 0.35))
    txt(d, (x0, y + 6), title, F(FB, 92), WHITE, (lt - 0.08) / 0.25, "lm")

def s_hook(d, t):
    lt = t - T["hook"]; k = back(lt / 0.4); a = cl(lt / 0.15)
    txt(d, (W / 2, 380), "MASZ JEDNO", F(FB, int(110 * (1.25 - 0.25 * k))), WHITE, a, "mm")
    txt(d, (W / 2, 500), "SPOJRZENIE", F(FB, int(110 * (1.25 - 0.25 * k))), WHITE, cl((lt - .1) / .15), "mm")
    lt2 = t - T["hook2"]
    sh = 6 * math.sin(lt2 * 60) * max(0, 1 - lt2 / 0.35) if lt2 > 0 else 0
    s2 = back(lt2 / 0.35)
    txt(d, (W / 2 + sh, 630), "REKRUTERA", F(FB, int(118 * (1.2 - 0.2 * s2))), LIME, cl(lt2 / .15), "mm")
    l3 = t - T["nie"]
    txt(d, (W / 2, 790 + 25 * (1 - eo(l3 / .3))), "Nie marnuj go na", F(FM, 54), GREY, l3 / .2, "mm")
    l4 = t - T["dzies"]
    for i in range(10):
        li = l4 - i * 0.06
        if li < 0: continue
        a = cl(li / .15); col, row = i % 5, i // 5
        x = 150 + col * 160; y = 880 + row * 150
        d.rounded_rectangle([x, y, x + 130, y + 110], 18, fill=(60, 70, 100, int(255 * a)))
        d.rounded_rectangle([x + 18, y + 22, x + 112, y + 34], 6, fill=(95, 105, 140, int(255 * a)))
        d.rounded_rectangle([x + 18, y + 50, x + 80, y + 60], 5, fill=(95, 105, 140, int(255 * a)))
    if l4 > 0.8:
        txt(d, (W / 2, 1230), "10 średnich projektów", F(FB, 58), WHITE, (l4 - .8) / .2, "mm")
        k = (l4 - 1.1) / .3
        w = d.textlength("10 średnich projektów", font=F(FB, 58))
        strike(d, W / 2 - w / 2, W / 2 + w / 2, 1236, k)

def s_raz(d, t):
    lt = t - T["raz"]; header(d, 1, "TOP 3", lt)
    l2 = t - T["top"]
    names = ["Dungeon Runner", "Neon Drift", "Tiny Tactics"]
    for i, n in enumerate(names):
        li = l2 - i * 0.3
        if li < 0: continue
        a = cl(li / .2); y = 520 + i * 150 + 30 * (1 - eo(li / .3))
        d.rounded_rectangle([110, y, W - 110, y + 120], 30, fill=(255, 255, 255, int(26 * a)), outline=LIME + (int(200 * a),), width=3)
        d.ellipse([140, y + 25, 210, y + 95], fill=LIME + (int(255 * a),))
        txt(d, (175, y + 62), str(i + 1), F(FB, 44), DARK, a, "mm")
        txt(d, (240, y + 60), n, F(FB, 52), WHITE, a, "lm")
    l3 = t - T["gora"]
    if l3 > 0:
        pill(d, W / 2, 1060 + 25 * (1 - eo(l3 / .3)), "NAJLEPSZE NA SAMEJ GÓRZE", F(FB, 50), l3 / .2)

def s_dwa(d, t):
    lt = t - T["dwa"]; header(d, 2, "TWOJA ROLA", lt)
    l2 = t - T["zdanie"]
    if l2 > -0.2:
        a = cl(l2 / .25); y0 = 500 + 40 * (1 - eo(l2 / .35))
        d.rounded_rectangle([90, y0, W - 90, y0 + 400], 36, fill=(255, 255, 255, int(20 * a)), outline=LIME + (int(200 * a),), width=4)
        txt(d, (140, y0 + 50), "Dungeon Runner · Unity", F(FM, 42), GREY, a)
        lines = ["Moja rola: AI przeciwników", "i system walki (C#)."]
        full = " | ".join(lines); n = int(len(full) * cl((l2 - .1) / 1.2))
        shown = full[:n].split(" | ")
        for j, s in enumerate(shown):
            txt(d, (140, y0 + 140 + j * 78), s, F(FB, 54), WHITE, a)
        l3 = t - T["ty"]
        if l3 > 0:
            check(d, 140, y0 + 310, 56, cl(l3 / .2))
            txt(d, (215, y0 + 338), "co dokładnie zrobiłeś TY", F(FM, 40), LIME, l3 / .2, "lm")

def s_trzy(d, t):
    lt = t - T["trzy"]; header(d, 3, "GAMEPLAY", lt)
    for key, lab, x in [("gif", "GIF", 300), ("wideo", "WIDEO", 700)]:
        l = t - T[key]
        if l > 0:
            k = back(l / .4)
            pill(d, x, 560, lab, F(FB, max(1, int(80 * k))), l / .15, padx=50, pady=28)
            # play icon
    l3 = t - T["zamiast"]
    if l3 > 0:
        txt(d, (W / 2, 740 + 25 * (1 - eo(l3 / .3))), "zamiast samych", F(FM, 54), GREY, l3 / .2, "mm")
        f = F(FB, 80); s = "screenów"; w = d.textlength(s, font=f)
        txt(d, (W / 2, 850 + 25 * (1 - eo((l3 - .15) / .3))), s, f, WHITE, (l3 - .15) / .2, "mm")
        strike(d, W / 2 - w / 2, W / 2 + w / 2, 858, (l3 - .6) / .3)
        for i in range(3):
            a = cl((l3 - .2 - i * .1) / .2); x = 190 + i * 250
            d.rounded_rectangle([x, 960, x + 200, 1090], 18, outline=(95, 105, 140, int(255 * a)), width=4)
            d.polygon([(x + 30, 1070), (x + 80, 1010), (x + 120, 1050), (x + 150, 1025), (x + 175, 1070)], fill=(95, 105, 140, int(255 * a)))

def s_link(d, t):
    lt = t - T["link"]
    txt(d, (W / 2, 330 + 30 * (1 - eo(lt / .3))), "Link do portfolio", F(FB, 80), WHITE, lt / .2, "mm")
    l2 = t - T["cv"]
    if l2 > -0.1:
        a = cl(l2 / .25); y0 = 450 + 40 * (1 - eo(l2 / .35))
        d.rounded_rectangle([140, y0, W - 140, y0 + 300], 30, fill=(255, 255, 255, int(235 * a)))
        txt(d, (190, y0 + 40), "CV", F(FB, 56), DARK, a)
        d.rounded_rectangle([190, y0 + 130, 600, y0 + 146], 8, fill=(200, 205, 220, int(255 * a)))
        txt(d, (190, y0 + 190), "artstation.com/twojnick", F(FB, 44), (30, 120, 70), a)
        check(d, W - 240, y0 + 30, 64, a)
    l3 = t - T["pdf"]
    if l3 > 0:
        f = F(FM, 52); s = "nie w PDF-ie na dnie maila"; w = d.textlength(s, font=f)
        txt(d, (W / 2, 870 + 25 * (1 - eo(l3 / .3))), s, f, GREY, l3 / .2, "mm")
        strike(d, W / 2 - w / 2, W / 2 + w / 2, 876, (l3 - .5) / .4)

def s_cta(d, t, frame):
    lt = t - T["cta"]; k = back(lt / .45); a = cl(lt / .2)
    lw = int(520 * max(k, .05)); lg = logo.resize((lw, max(1, int(logo.height * lw / logo.width))), Image.LANCZOS)
    lg.putalpha(lg.split()[3].point(lambda v: int(v * a)))
    frame.alpha_composite(lg, (int(W / 2 - lw / 2), int(420 - lg.height / 2)))
    txt(d, (W / 2, 600), "workplays.it", F(FB, 120), LIME, (lt - .2) / .2, "mm")
    l4 = lt - .55
    txt(d, (W / 2, 715 + 25 * (1 - eo(l4 / .3))), "Praca w gamedevie", F(FM, 58), WHITE, l4 / .25, "mm")
    l3 = lt - .9; bob = 6 * math.sin(lt * 6) if l3 > .4 else 0
    pill(d, W / 2, 850 + bob + 30 * (1 - eo(l3 / .3)), "Daj się znaleźć  >", F(FB, 60), l3 / .2, padx=50, pady=26)

DRAW = dict(hook=s_hook, raz=s_raz, dwa=s_dwa, trzy=s_trzy, link=s_link)
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

BUST = 600; BH = 550
BX, BY = W - BUST + 30, H - BH
GLOW = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(GLOW).ellipse([BX + 90, BY + 60, BX + BUST - 90, BY + BUST + 120], fill=(80, 130, 255, 70))
GLOW = GLOW.filter(ImageFilter.GaussianBlur(60))

def main():
    src, out = sys.argv[1], sys.argv[2]
    previews = [float(x) for x in sys.argv[3:]]
    keycol = sys.argv and __import__("os").environ.get("KEYCOL", "0x00A73C")
    if src == "none":
        mf = None
    else:
        mf = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf",
            f"fps={FPS},crop=960:880:0:0,colorkey={keycol}:0.26:0.10,despill=type=green,scale={BUST}:{BH}",
            "-pix_fmt", "rgba", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    enc = None
    if not previews:
        enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n = int(END * FPS); last = None; fsz = BUST * BH * 4
    for i in range(n):
        t = i / FPS
        if mf:
            raw = mf.stdout.read(fsz)
            if raw and len(raw) == fsz: last = Image.frombytes("RGBA", (BUST, BH), raw)
        if previews and not any(abs(t - p) < 0.5 / FPS for p in previews): continue
        fr = bg(t); board(t, fr); fr.alpha_composite(GLOW)
        if last is not None:
            ent = eo(t / 0.35); fr.alpha_composite(last, (BX, int(BY + (1 - ent) * 200)))
        if previews: fr.convert("RGB").save(f"prev_{t:05.2f}.jpg", quality=85)
        else: enc.stdin.write(fr.tobytes())
    if mf: mf.stdout.close(); mf.wait()
    if enc: enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    main()
