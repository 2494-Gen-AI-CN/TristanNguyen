"""Builds the 🚨 sprite used for live cells, as an RGBA float array."""

import os

import numpy as np

EMOJI = "\U0001F6A8"  # 🚨
EMOJI_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "C:/Windows/Fonts/seguiemj.ttf",
]


def _emoji_sprite(px):
    from PIL import Image, ImageDraw, ImageFont

    for path in EMOJI_FONTS:
        if not os.path.exists(path):
            continue
        for size in (109, 160, 96, 64):  # bitmap emoji fonts only accept certain sizes
            try:
                font = ImageFont.truetype(path, size)
                break
            except OSError:
                font = None
        if font is None:
            continue
        img = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((size // 4, size // 4), EMOJI, font=font, embedded_color=True)
        bbox = img.getbbox()
        if not bbox:
            continue
        img = img.crop(bbox)
        side = max(img.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        square = square.resize((px, px), Image.LANCZOS)
        return np.asarray(square, dtype=np.float32) / 255.0
    return None


def _drawn_sprite(px):
    """Fallback siren drawn with numpy: red dome on a grey base."""
    y, x = np.mgrid[0:px, 0:px] / (px - 1)
    rgba = np.zeros((px, px, 4), dtype=np.float32)
    dome = ((x - 0.5) ** 2 / 0.12 + (y - 0.62) ** 2 / 0.25 <= 1) & (y <= 0.75)
    base = (y > 0.75) & (y < 0.92) & (x > 0.12) & (x < 0.88)
    shine = (x - 0.38) ** 2 + (y - 0.45) ** 2 < 0.008
    rgba[dome] = (0.9, 0.1, 0.1, 1)
    rgba[shine & dome] = (1, 0.85, 0.85, 1)
    rgba[base] = (0.55, 0.55, 0.6, 1)
    return rgba


def make_alarm_sprite(px=16):
    try:
        sprite = _emoji_sprite(px)
    except Exception:
        sprite = None
    return sprite if sprite is not None else _drawn_sprite(px)
