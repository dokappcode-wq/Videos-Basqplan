"""Monta el vídeo de presentación de Basqplan (formato TikTok 9:16).

Estructura (calcada del vídeo de referencia, 11 s):
  1. 0.0–1.2 s  Foto a pantalla completa + "BIENVENIDOS A" en serif pequeño.
  2. 1.2–6.3 s  Collage de 3 franjas horizontales que van entrando y cambiando
                de foto a ritmo; en la franja central aparece el nombre de marca.
  3. 6.3–11.2 s Cortes rápidos a pantalla completa (~0.6 s por plano) y cierre
                con el nombre de la marca.

Uso:  python3 scripts/build_video.py [salida.mp4]
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logo import render_logo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PHOTOS, FONTS = ROOT / "photos", ROOT / "fonts"
W, H, FPS = 1080, 1920, 30
BAND = H // 3

# ---------------------------------------------------------------- textos
TEXT_SMALL = "BIENVENIDOS A"    # línea pequeña (en la referencia: "ONGI ETORRI")
TEXT_BIG = "BASQPLAN"           # nombre de marca (en la referencia: "EUSKAL HERRIRA")
TEXT_END = "BASQPLAN"           # cierre
TEXT_END_SUB = "PAÍS VASCO"     # subtítulo del cierre

# ---------------------------------------------------------------- guion
# Fase 2: franjas. Cada evento: (segundo, franja 0/1/2 o "full", foto, animación)
INTRO = "otzarreta_vert"
BANDS = [
    (1.2, 0, "anboto", "slide_down"),
    (2.2, 2, "urkiola_caballos", "slide_up"),
    (3.2, 1, "gaztelugatxe1", "cut"),        # aquí entra el nombre de marca
    (4.2, 0, "gaztelugatxe_ilun", "cut"),
    (5.2, 2, "donostia", "cut"),
]
TITLE_FROM = 3.2
MONTAGE_START = 6.3
MONTAGE = ["gaztelugatxe_vert", "hondarribia_vert", "pasaia", "guggenheim_vert",
           "otzarreta", "urkiola_cruces", "getaria_ilun", "gaztelugatxe2"]
SHOT = 0.6
END_SHOT = "gaztelugatxe_ilun"   # último plano, con el cierre de marca
END_LEN = 3.5
DURATION = MONTAGE_START + len(MONTAGE) * SHOT + END_LEN


# ---------------------------------------------------------------- utilidades
_cache = {}
def photo(name):
    if name not in _cache:
        im = Image.open(PHOTOS / f"{name}.jpg").convert("RGB")
        # Look "móvil / CapCut": algo más de contraste y saturación.
        a = np.asarray(im).astype(np.float32) / 255
        a = np.clip((a - 0.5) * 1.04 + 0.5, 0, 1)
        g = a.mean(axis=2, keepdims=True)
        a = np.clip(g + (a - g) * 1.05, 0, 1)
        _cache[name] = Image.fromarray((a * 255).astype(np.uint8))
    return _cache[name]


def cover(name, w, h, t, zoom=0.06, pan=(0.5, 0.5)):
    """Recorta la foto para cubrir w×h con un zoom lento (t en 0..1)."""
    im = photo(name)
    s = max(w / im.width, h / im.height) * (1 + zoom * t)
    cw, ch = w / s, h / s
    x0 = (im.width - cw) * pan[0]
    y0 = (im.height - ch) * pan[1]
    return im.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


F_SMALL = font("CormorantGaramond_600SemiBold.ttf", 46)
F_BIG = font("CormorantGaramond_500Medium.ttf", 104)
F_SUB = font("Montserrat_500Medium.ttf", 30)
F_END = font("CormorantGaramond_500Medium.ttf", 84)

# Logo para el cierre: azul marino → blanco para que se vea sobre fondo oscuro; el dorado se mantiene.
LOGO_W = 620
LOGO = render_logo(LOGO_W, {"#033455": "#FFFFFF"})


def spaced(draw, text, f, tracking):
    """Devuelve las posiciones de cada letra con espaciado (tracking en px)."""
    xs, x = [], 0
    for ch in text:
        xs.append(x)
        x += draw.textlength(ch, font=f) + tracking
    return xs, x - tracking


def draw_text(img, lines, cy, alpha=1.0):
    """lines: [(texto, fuente, tracking[, opacidad])], centradas verticalmente en cy."""
    lines = [l if len(l) == 4 else (*l, 1.0) for l in lines]
    if alpha <= 0:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    heights = [f.getbbox("HÁ")[3] for _, f, _, _ in lines]
    gap = 18
    total = sum(heights) + gap * (len(lines) - 1)
    y = cy - total / 2
    for (txt, f, tr, la), h in zip(lines, heights):
        xs, tw = spaced(d, txt, f, tr)
        x0 = (W - tw) / 2
        for ch, x in zip(txt, xs):
            d.text((x0 + x, y), ch, font=f, fill=(255, 255, 255, int(255 * alpha * la)))
        y += h + gap
    # sombra suave para que se lea sobre cualquier foto
    a_ch = layer.getchannel("A")
    out = img.convert("RGBA")
    # halo difuso amplio + sombra cercana más marcada
    for blur, op, dy in ((22, 0.55, 0), (5, 0.75, 2)):
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow.putalpha(a_ch.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(blur))
                        .point(lambda v, op=op: int(min(255, v * op * 1.6))))
        out.alpha_composite(shadow, (0, dy))
    out.alpha_composite(layer)
    return out.convert("RGB")


# ---------------------------------------------------------------- fotogramas
def band_state(t):
    """Qué foto hay en cada franja en el instante t y cuándo entró."""
    state = [None, None, None]
    for (ts, b, name, anim) in BANDS:
        if t >= ts:
            state[b] = (name, ts, anim)
    return state


def frame(t):
    # --- Fase 1: intro a pantalla completa
    if t < BANDS[0][0]:
        img = cover(INTRO, W, H, t / BANDS[0][0] * 0.4, pan=(0.5, 0.45))
        return draw_text(img, [(TEXT_SMALL, F_SMALL, 10)], H * 0.47, ease(t / 0.35))

    # --- Fase 2: collage de franjas
    if t < MONTAGE_START:
        prog = (t - BANDS[0][0]) / (MONTAGE_START - BANDS[0][0])
        # la foto de la intro sigue de fondo y las franjas entran por encima
        img = cover(INTRO, W, H, 0.4 + prog * 0.6, pan=(0.5, 0.45))
        state = band_state(t)
        for b in (0, 2, 1):
            if state[b] is None:
                continue
            name, ts, anim = state[b]
            p = ease((t - ts) / 0.32)
            tile = cover(name, W, BAND, (t - ts) / 3.0, zoom=0.08)
            y = b * BAND
            if anim == "slide_down":
                y = int(-BAND + (BAND + y) * p)
            elif anim == "slide_up":
                y = int(H - (H - y) * p)
            img.paste(tile, (0, y))
        # texto: solo "ONGI ETORRI" hasta que entra la marca
        if t < TITLE_FROM:
            return draw_text(img, [(TEXT_SMALL, F_SMALL, 10)], H * 0.47)
        a = ease((t - TITLE_FROM) / 0.3)
        return draw_text(img, [(TEXT_SMALL, F_SMALL, 10), (TEXT_BIG, F_BIG, 6, a)], H / 2)

    # --- Fase 3: montaje rápido a pantalla completa
    i = int((t - MONTAGE_START) // SHOT)
    if i < len(MONTAGE):
        local = (t - MONTAGE_START - i * SHOT) / SHOT
        return cover(MONTAGE[i], W, H, local, zoom=0.05)

    # --- Cierre de marca
    ts = MONTAGE_START + len(MONTAGE) * SHOT
    local = (t - ts) / END_LEN
    img = cover(END_SHOT, W, H, local, zoom=0.05)
    dark = ease((t - ts) / 0.4) * 0.35
    img = Image.blend(img, Image.new("RGB", img.size), dark)
    # logo (fondo transparente) con fundido y ligero zoom de entrada
    a = ease((t - ts) / 0.5)
    lw = int(LOGO_W * (0.92 + 0.08 * a))
    logo = LOGO.resize((lw, round(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
    logo.putalpha(logo.getchannel("A").point(lambda v: int(v * a)))
    out = img.convert("RGBA")
    out.alpha_composite(logo, ((W - logo.width) // 2, int(H * 0.40 - logo.height / 2)))
    ta = ease((t - ts - 0.25) / 0.4)
    return draw_text(out.convert("RGB"), [(TEXT_END, F_END, 8), (TEXT_END_SUB, F_SUB, 12)], H * 0.40 + 290, ta)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "basqplan_presentacion.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = round(DURATION * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{DURATION}", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(np.asarray(frame(k / FPS), dtype=np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    print(f"{out}  ({n} fotogramas, {DURATION:.1f} s)")


if __name__ == "__main__":
    main()
