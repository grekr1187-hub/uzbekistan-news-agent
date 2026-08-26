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
