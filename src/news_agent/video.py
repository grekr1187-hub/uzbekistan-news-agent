from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(" ".join(text.split()), width=width, break_long_words=False)


def make_news_image(title: str, body: str, output_path: str) -> str:
    """Create a free branded vertical news image locally from the generated story text."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1080, 1350
    image = Image.new("RGB", (width, height), (10, 18, 32))
    pixels = image.load()
    for y in range(height):
        blend = y / max(height - 1, 1)
        r = int(10 + 8 * blend)
        g = int(18 + 20 * blend)
        b = int(32 + 28 * blend)
        for x in range(width):
            pixels[x, y] = (r, g, b)

    draw = ImageDraw.Draw(image)
    title_font = _font(62)
    body_font = _font(34)
    small_font = _font(27)

    draw.rounded_rectangle((55, 55, width - 55, 160), radius=28, fill=(23, 47, 72))
    draw.text((88, 88), "🇺🇿  УЗБЕКИСТАН СЛУШАЕТ", font=small_font, fill="white")
    draw.rounded_rectangle((55, 195, 190, 211), radius=8, fill=(255, 255, 255))

    title_lines = _wrap(title, 25)[:6]
    body_lines = _wrap(body, 43)[:9]

    y = 265
    for line in title_lines:
        draw.text((65, y), line, font=title_font, fill="white")
        y += 78

    y += 35
    for line in body_lines:
        draw.text((65, y), line, font=body_font, fill=(225, 235, 245))
        y += 48

    draw.rounded_rectangle((55, height - 155, width - 55, height - 55), radius=24, fill=(18, 34, 52))
    draw.text((82, height - 125), "Новости Узбекистана  •  AI-редактор", font=small_font, fill=(185, 200, 218))

    image.save(out, format="JPEG", quality=92, optimize=True)
    return str(out)


def make_news_video(title: str, body: str, output_path: str, seconds: int = 8) -> str:
    """Create a free vertical news short locally; no paid video API is required."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        frame_dir = Path(tmp) / "frames"
        frame_dir.mkdir()
        title_font, body_font, small_font = _font(60), _font(36), _font(26)
        frames = 24 * seconds
        title_lines, body_lines = _wrap(title, 22)[:5], _wrap(body, 34)[:8]
        for i in range(frames):
            im = Image.new("RGB", (720, 1280), (12, 20, 35))
            draw = ImageDraw.Draw(im)
            y = 80 - int(18 * i / max(frames - 1, 1))
            draw.text((45, y), "UZBEKISTAN NEWS", font=small_font, fill="white")
            y = 190
            for line in title_lines:
                draw.text((45, y), line, font=title_font, fill="white")
                y += 72
            y += 30
            for line in body_lines:
                draw.text((45, y), line, font=body_font, fill=(225, 235, 245))
                y += 46
            draw.text((45, 1175), "Источник: открытые СМИ • AI редактор", font=small_font, fill=(170, 185, 205))
            im.save(frame_dir / f"frame_{i:05d}.png", quality=92)
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([
            ffmpeg, "-y", "-framerate", "24", "-i", str(frame_dir / "frame_%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return str(out)
