import io
from pathlib import Path
import hashlib
import cairosvg
from PIL import Image


# -------------------------------------------------------
# HASH (to avoid re-conversion)
# -------------------------------------------------------

def file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# -------------------------------------------------------
# SVG → PNG (cached)
# -------------------------------------------------------

def svg_to_png(svg_path: str) -> str:
    """
    Converts SVG to PNG and returns PNG path.
    Caches result using file hash.
    """

    svg_path = Path(svg_path)
    h = file_hash(str(svg_path))

    png_path = svg_path.with_name(f"{svg_path.stem}__{h[:10]}.png")

    if png_path.exists():
        return str(png_path)

    png_bytes = cairosvg.svg2png(url=str(svg_path))

    with open(png_path, "wb") as f:
        f.write(png_bytes)

    return str(png_path)