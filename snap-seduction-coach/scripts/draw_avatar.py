#!/usr/bin/env python3
"""Dessine VEXA, la mascotte holographique du skill (personnage original,
style néon cyberpunk « IA dans une puce »), en 3 expressions JPEG.

Usage : python3 draw_avatar.py [dossier_sortie]   (défaut : ../assets)
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

W = H = 512
CYAN = (0, 240, 255)
MAGENTA = (255, 40, 170)
YELLOW = (250, 240, 60)
INK = (12, 8, 24)


def background():
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    # dégradé vertical violet nuit
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(20 + 30 * t), int(6 + 4 * t), int(40 + 30 * t)))
    # grille en perspective (sol)
    horizon = 360
    for i in range(-12, 13):
        d.line([(W / 2 + i * 12, horizon), (W / 2 + i * 90, H)], fill=(120, 20, 110), width=1)
    y, step = horizon, 4
    while y < H:
        d.line([(0, y), (W, y)], fill=(120, 20, 110), width=1)
        y += step
        step *= 1.35
    # skyline
    rnd = random.Random(7)
    x = 0
    while x < W:
        bw, bh = rnd.randint(18, 46), rnd.randint(60, 190)
        d.rectangle([x, horizon - bh, x + bw, horizon], fill=(18, 10, 36))
        for wy in range(horizon - bh + 8, horizon - 6, 10):
            for wx in range(x + 4, x + bw - 4, 8):
                if rnd.random() < 0.25:
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=rnd.choice([CYAN, MAGENTA, YELLOW]))
        x += bw + 2
    return img


def glow_layer(draw_fn, color, radius=10):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), color + (255,))
    return layer.filter(ImageFilter.GaussianBlur(radius))


def character(expr):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = 256, 220
    skin = (255, 214, 220, 255)
    hair_dark, hair_light = (70, 0, 120, 255), (190, 40, 255, 255)

    # buste / veste
    d.polygon([(150, 470), (190, 330), (322, 330), (362, 470)], fill=(25, 20, 45, 255))
    d.polygon([(190, 330), (256, 400), (322, 330)], fill=(255, 214, 220, 255))
    d.line([(190, 330), (150, 470)], fill=CYAN + (255,), width=4)
    d.line([(322, 330), (362, 470)], fill=MAGENTA + (255,), width=4)
    # cou
    d.rectangle([236, 290, 276, 335], fill=skin)
    d.line([(236, 318), (276, 318)], fill=CYAN + (255,), width=3)  # collier néon
    # cheveux arrière (carré plongeant)
    d.polygon([(150, 200), (170, 120), (256, 80), (342, 120), (362, 200), (370, 320), (300, 300),
               (212, 300), (142, 320)], fill=hair_dark)
    # visage
    d.ellipse([cx - 82, cy - 90, cx + 82, cy + 85], fill=skin)
    # frange asymétrique
    d.polygon([(168, 175), (180, 110), (256, 86), (338, 112), (350, 170), (300, 140), (270, 165),
               (240, 135), (205, 168)], fill=hair_light)
    d.polygon([(338, 112), (360, 210), (345, 260), (340, 170)], fill=hair_light)
    d.line([(195, 120), (250, 95)], fill=(255, 150, 255, 255), width=3)  # reflet
    # yeux
    ey = cy + 5
    for ex, side in ((cx - 36, -1), (cx + 36, 1)):
        if expr == "wink" and side == 1:
            d.arc([ex - 20, ey - 8, ex + 20, ey + 16], 200, 340, fill=INK + (255,), width=5)
            continue
        h = 10 if expr == "alert" else 18
        d.ellipse([ex - 18, ey - h, ex + 18, ey + h], fill=(255, 255, 255, 255))
        d.ellipse([ex - 11, ey - h + 2, ex + 11, ey + h - 2], fill=CYAN + (255,))
        d.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=INK + (255,))
        d.ellipse([ex + 2, ey - 9, ex + 7, ey - 4], fill=(255, 255, 255, 255))
        d.line([(ex - 20, ey - h - 2), (ex + 18, ey - h - 6)], fill=INK + (255,), width=4)
    # sourcils
    if expr == "alert":
        d.line([(cx - 56, ey - 30), (cx - 18, ey - 22)], fill=hair_dark, width=5)
        d.line([(cx + 56, ey - 30), (cx + 18, ey - 22)], fill=hair_dark, width=5)
    # joues
    for bx in (cx - 52, cx + 52):
        d.ellipse([bx - 14, ey + 26, bx + 14, ey + 36], fill=(255, 120, 170, 160))
    # bouche
    my = cy + 52
    if expr == "alert":
        d.ellipse([cx - 8, my - 6, cx + 8, my + 8], fill=(150, 30, 70, 255))
    else:
        d.arc([cx - 18, my - 14, cx + 18, my + 8], 20, 160, fill=(170, 30, 80, 255), width=4)
    # implants / tatouage circuit sur la tempe
    for i, (x0, y0) in enumerate([(180, 230), (186, 246), (176, 262)]):
        d.line([(x0, y0), (x0 + 14, y0)], fill=CYAN + (255,), width=2)
        d.ellipse([x0 + 13, y0 - 3, x0 + 19, y0 + 3], fill=CYAN + (255,))
    # puce de données tenue près du visage
    chip = [(380, 300), (440, 300), (440, 360), (380, 360)]
    d.rectangle([380, 300, 440, 360], fill=(20, 30, 40, 255), outline=YELLOW + (255,), width=3)
    for k in range(4):
        d.line([(388 + k * 14, 300), (388 + k * 14, 290)], fill=YELLOW + (255,), width=2)
        d.line([(388 + k * 14, 360), (388 + k * 14, 370)], fill=YELLOW + (255,), width=2)
    d.text((394, 322), "LOVE", fill=MAGENTA + (255,))
    return layer, chip


def hologram_fx(img):
    """Aberration chromatique + scanlines pour l'effet hologramme."""
    r, g, b = img.split()
    r = r.transform(img.size, Image.AFFINE, (1, 0, -3, 0, 1, 0))
    b = b.transform(img.size, Image.AFFINE, (1, 0, 3, 0, 1, 0))
    img = Image.merge("RGB", (r, g, b))
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(0, H, 3):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 55))
    # bandes de glitch
    rnd = random.Random(3)
    for _ in range(5):
        y = rnd.randint(60, 460)
        h = rnd.randint(3, 9)
        band = img.crop((0, y, W, y + h))
        img.paste(band, (rnd.randint(-14, 14), y))
    return img


def frame(img, label, color):
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, W - 7, H - 7], outline=color, width=3)
    for (x, y, dx, dy) in ((6, 6, 1, 1), (W - 7, 6, -1, 1), (6, H - 7, 1, -1), (W - 7, H - 7, -1, -1)):
        d.line([(x, y), (x + 40 * dx, y)], fill=YELLOW, width=6)
        d.line([(x, y), (x, y + 40 * dy)], fill=YELLOW, width=6)
    d.rectangle([20, 20, 20 + 8 * len(label) + 16, 42], fill=color)
    d.text((28, 26), label, fill=INK)
    d.text((W - 150, H - 30), "VEXA.OS // v2.077", fill=CYAN)
    return img


def render(expr, label, color):
    base = background().convert("RGBA")
    char, chip = character(expr)
    # halo néon autour du personnage
    alpha = char.split()[3]
    halo = Image.new("RGBA", (W, H), color + (0,))
    halo.putalpha(alpha.filter(ImageFilter.GaussianBlur(14)))
    base = Image.alpha_composite(base, halo)
    base = Image.alpha_composite(base, glow_layer(lambda d, c: d.rectangle([370, 290, 450, 370], fill=c),
                                                  YELLOW, 16))
    base = Image.alpha_composite(base, char)
    out = hologram_fx(base.convert("RGB"))
    return frame(out, label, color)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    for expr, label, color in (("neutral", "SCAN // ANALYSE", CYAN),
                               ("wink", "SIGNAL // POSITIF", MAGENTA),
                               ("alert", "ATTENTION // DRAPEAU", YELLOW)):
        path = os.path.join(out_dir, f"vexa-{expr}.jpg")
        render(expr, label, color).save(path, "JPEG", quality=90)
        print(path)


if __name__ == "__main__":
    main()
