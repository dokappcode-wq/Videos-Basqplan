"""Monta el vídeo de presentación de Basqplan (formato TikTok 9:16) con música y voz en off.

Estructura (inspirada en el vídeo de referencia), sincronizada a la música (96 BPM, 1 tiempo = 0,625 s):
  1. 0.00–1.25 s   Foto a pantalla completa + "WELCOME TO" en serif pequeño.
  2. 1.25–7.50 s   Collage de 3 franjas que entran y cambian de foto cada 2 tiempos;
                   en la franja central aparece "BASQUE COUNTRY".
  3. 7.50–22.5 s   Entra la base de la música: montaje a pantalla completa al ritmo.
  4. 22.5–27.0 s   Cierre con el logo de Basqplan.
La locución (audio/vo_XX.wav, ver scripts/voiceover.py) se coloca según VOICE.

Uso:  python3 scripts/build_video.py [salida.mp4]
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logo import render_logo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PHOTOS, FONTS, AUDIO = ROOT / "photos", ROOT / "fonts", ROOT / "audio"
W, H, FPS = 1080, 1920, 30
BAND = H // 3
BEAT = 60 / 96

# ---------------------------------------------------------------- textos
TEXT_SMALL = "WELCOME TO"        # línea pequeña (en la referencia: "ONGI ETORRI")
TEXT_BIG = "BASQUE COUNTRY"      # línea grande (en la referencia: "EUSKAL HERRIRA")
TEXT_END = "BASQPLAN"            # cierre, bajo el logo
TEXT_END_SUB = "EUSKADI"         # subtítulo del cierre

# ---------------------------------------------------------------- guion
INTRO = "otzarreta_vert"
# Franjas: (segundo, franja 0=arriba 1=centro 2=abajo, foto, animación)
BANDS = [
    (2 * BEAT, 0, "anboto", "slide_down"),
    (4 * BEAT, 2, "urkiola_caballos", "slide_up"),
    (6 * BEAT, 1, "gaztelugatxe1", "cut"),        # aquí entra "BASQUE COUNTRY"
    (8 * BEAT, 0, "pasaia", "cut"),
    (10 * BEAT, 2, "donostia", "cut"),
]
TITLE_FROM = 6 * BEAT
MONTAGE_START = 12 * BEAT
# Montaje: (foto, duración en tiempos). Suma = 24 tiempos (6 compases).
MONTAGE = [
    ("zumaia_vert", 2), ("gaztelugatxe_vert", 2), ("costa_zumaia", 2),   # "Acantilados..."
    ("otzarreta", 4),                                                    # "Bosques..."
    ("urkiola_cruces", 2), ("elantxobe", 2), ("hondarribia_vert", 2),    # "Montañas, pueblos marineros,"
    ("getaria_ilun", 2),                                                 # "...y atardeceres"
    ("concha", 2),                                                       # "Esto es Euskadi."
    ("bilbao_noche", 1), ("pintxos", 1), ("guggenheim_vert", 1), ("itzurun", 1),
]
END_SHOT = "gaztelugatxe_ilun"   # último plano, con el logo
END_START = MONTAGE_START + sum(b for _, b in MONTAGE) * BEAT
END_LEN = 4.5
DURATION = END_START + END_LEN

# Locución: (archivo, segundo en que empieza)
VOICE = [
    ("vo_00.wav", 0.35),    # Hay lugares que se miran... y lugares que se sienten.
    ("vo_01.wav", 7.70),    # Acantilados que se asoman al mar.
    ("vo_02.wav", 11.40),   # Bosques que parecen sacados de un cuento.
    ("vo_03.wav", 14.00),   # Montañas, pueblos marineros, y atardeceres que no se olvidan.
    ("vo_04.wav", 19.00),   # Esto es Euskadi.
    ("vo_05.wav", END_START + 0.9),  # Descúbrelo con Basqplan.
]


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
F_BIG = font("CormorantGaramond_500Medium.ttf", 92)
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
        # texto: solo la línea pequeña hasta que entra la grande
        if t < TITLE_FROM:
            return draw_text(img, [(TEXT_SMALL, F_SMALL, 10)], H * 0.47)
        a = ease((t - TITLE_FROM) / 0.3)
        return draw_text(img, [(TEXT_SMALL, F_SMALL, 10), (TEXT_BIG, F_BIG, 6, a)], H / 2)

    # --- Fase 3: montaje a pantalla completa, al ritmo de la música
    if t < END_START:
        ts = MONTAGE_START
        for name, beats in MONTAGE:
            d = beats * BEAT
            if t < ts + d:
                return cover(name, W, H, (t - ts) / d, zoom=0.04 + 0.02 * beats)
            ts += d

    # --- Cierre de marca
    ts = END_START
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


def mix_audio():
    """Mezcla música + locución; la música baja automáticamente cuando habla la voz."""
    dest = AUDIO / "mix.wav"
    inputs = ["-i", str(AUDIO / "music.wav")]
    chains = []
    for k, (f, start) in enumerate(VOICE, start=1):
        inputs += ["-i", str(AUDIO / f)]
        ms = int(start * 1000)
        chains.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
    n = len(VOICE)
    vo = "".join(f"[v{k}]" for k in range(1, n + 1))
    graph = ";".join(chains + [
        f"{vo}amix=inputs={n}:normalize=0,highpass=f=80,"
        "equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3,volume=1.6,asplit=2[vo][sc]",
        "[0:a]volume=0.8[mus]",
        "[mus][sc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=500[duck]",
        f"[duck][vo]amix=inputs=2:normalize=0,alimiter=limit=0.95,apad,atrim=0:{DURATION:.3f}[out]",
    ])
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph,
                    "-map", "[out]", "-ar", "44100", str(dest)], check=True)
    return dest


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "basqplan_presentacion.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = round(DURATION * FPS)
    audio = mix_audio()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(audio),
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{DURATION:.3f}", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(np.asarray(frame(k / FPS), dtype=np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    print(f"{out}  ({n} fotogramas, {DURATION:.1f} s)")


if __name__ == "__main__":
    main()
