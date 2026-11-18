#!/usr/bin/env python3
"""Narzędzia do póz maskotki wygenerowanych w ElevenLabs (jednolite tło -> PNG z alfą,
naklejanie treści na trzymaną kartę z perspektywą).

  cutout(path)            -> RGBA pełnego rozmiaru (tło usunięte flood-fillem od krawędzi)
  card_quad(path)         -> 4 rogi białej karty (tl, tr, br, bl) w pikselach obrazu
  put_on_card(fig, quad, card_img, inset) -> fig z treścią zmapowaną na kartę
"""
from collections import deque
import numpy as np
from PIL import Image, ImageFilter


def cutout(path, tol=22):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    bg = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
    cand = np.abs(a - bg).sum(2) < tol
    mask = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if cand[y, x]:
                mask[y, x] = 1; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if cand[y, x] and not mask[y, x]:
                mask[y, x] = 1; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and cand[ny, nx] and not mask[ny, nx]:
                mask[ny, nx] = 1; q.append((ny, nx))
    alpha = Image.fromarray(((~mask) * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out


def card_quad(path, thr=246):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    ys, xs = np.where(a.min(2) > thr)
    s, d = xs + ys, xs - ys
    return [(xs[s.argmin()], ys[s.argmin()]), (xs[d.argmax()], ys[d.argmax()]),
            (xs[s.argmax()], ys[s.argmax()]), (xs[d.argmin()], ys[d.argmin()])]


def _coeffs(dst, src):
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y]); B.append(X)
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y]); B.append(Y)
    return tuple(np.linalg.solve(np.array(A, float), np.array(B, float)))


def put_on_card(fig, quad, card_img, inset=0.06):
    cx = sum(p[0] for p in quad) / 4; cy = sum(p[1] for p in quad) / 4
    q = [(p[0] + (cx - p[0]) * inset, p[1] + (cy - p[1]) * inset) for p in quad]
    W, H = card_img.size
    warp = card_img.transform(fig.size, Image.PERSPECTIVE, _coeffs(q, [(0, 0), (W, 0), (W, H), (0, H)]), Image.BICUBIC)
    out = fig.copy()
    out.alpha_composite(warp)
    return out
