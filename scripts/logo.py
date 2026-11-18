"""Renderiza brand/logo_bp.svg (solo trazados M/L/Z, fill-rule evenodd) a una imagen RGBA
con fondo transparente, recortada a su contenido."""
import re
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

SVG = Path(__file__).resolve().parent.parent / "brand" / "logo_bp.svg"


def _paths(svg_text):
    for fill, d in re.findall(r'<path[^>]*fill="(#[0-9A-Fa-f]{6})"[^>]*d="([^"]+)"', svg_text):
        polys = []
        for sub in re.split(r"[Zz]", d):
            pts = [tuple(map(float, p)) for p in re.findall(r"(-?[\d.]+),(-?[\d.]+)", sub)]
            if len(pts) >= 3:
                polys.append(pts)
        yield fill, polys


def render_logo(width, colors=None, ss=4, svg=None):
    """colors: dict para recolorear, p. ej. {"#033455": "#FFFFFF"}. svg: ruta a otro SVG (por defecto el original)."""
    text = Path(svg).read_text() if svg else SVG.read_text()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', text).group(1).split()]
    scale = width * ss / vb[2]
    size = (int(vb[2] * scale), int(vb[3] * scale))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    for fill, polys in _paths(text):
        mask = Image.new("1", size, 0)
        for poly in polys:  # evenodd: cada subtrazado alterna dentro/fuera
            m = Image.new("1", size, 0)
            ImageDraw.Draw(m).polygon([((x - vb[0]) * scale, (y - vb[1]) * scale) for x, y in poly], fill=1)
            mask = ImageChops.logical_xor(mask, m)
        color = (colors or {}).get(fill.upper(), fill)
        out.paste(Image.new("RGBA", size, color), (0, 0), mask.convert("L"))
    out = out.crop(out.getbbox())
    return out.resize((max(1, out.width // ss), max(1, out.height // ss)), Image.LANCZOS)


if __name__ == "__main__":
    dest = SVG.parent
    render_logo(1200).save(dest / "logo_bp.png")
    render_logo(1200, {"#033455": "#FFFFFF"}).save(dest / "logo_bp_blanco.png")
    print("ok")
