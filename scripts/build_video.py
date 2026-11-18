"""Monta el vídeo de presentación de Basqplan (formato TikTok 9:16, ~16 s).

Estructura (inspirada en el vídeo de referencia; 1 tiempo = 0,625 s a 96 BPM):
  1. 0.0–2.0 s    Latidos de corazón: la foto se ilumina con cada latido + "WELCOME TO".
  2. 2.0–4.5 s    Collage de 3 franjas que entran a ritmo; aparece "BASQUE COUNTRY".
  3. 4.5–12.0 s   Montaje a pantalla completa con la voz en off.
  4. 12.0–16.0 s  Cierre: logo + "¿Preparados para descubrir Euskadi?".

Genera dos versiones:
  output/basqplan_para_tiktok.mp4   latidos + voz, SIN música → añadir la canción en TikTok
  output/basqplan_presentacion.mp4  latidos + música original + voz

Uso:  python3 scripts/build_video.py
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logo import render_logo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PHOTOS, FONTS, AUDIO, CLIPS = ROOT / "photos", ROOT / "fonts", ROOT / "audio", ROOT / "clips"
W, H, FPS = 1080, 1920, 30
BAND = H // 3
BEAT = 60 / 96

# ---------------------------------------------------------------- textos
TEXT_SMALL = "WELCOME TO"        # línea pequeña (en la referencia: "ONGI ETORRI")
TEXT_BIG = "BASQUE COUNTRY"      # línea grande (en la referencia: "EUSKAL HERRIRA")
TEXT_END = "BASQPLAN"            # cierre, bajo el logo
TEXT_END_Q = ["¿PREPARADOS PARA", "DESCUBRIR EUSKADI?"]

# ---------------------------------------------------------------- guion
HEARTBEATS = [0.15, 1.05]        # mismos tiempos que en compose_music.py
MUSIC_START = 2.0                # la música (o la canción en TikTok) entra aquí
INTRO = "otzarreta_vert"
# Franjas: (segundo, franja 0=arriba 1=centro 2=abajo, foto, animación)
BANDS = [
    (MUSIC_START, 0, "anboto", "slide_down"),
    (MUSIC_START + 1 * BEAT, 2, "urkiola_caballos", "slide_up"),
    (MUSIC_START + 2 * BEAT, 1, "gaztelugatxe1", "cut"),        # aquí entra "BASQUE COUNTRY"
    (MUSIC_START + 3 * BEAT, 0, "pasaia", "cut"),
]
TITLE_FROM = MUSIC_START + 2 * BEAT
MONTAGE_START = MUSIC_START + 4 * BEAT
# Montaje: (foto o "clip:nombre@segundo", duración en tiempos). Suma = 12 tiempos (3 compases).
# Las fotos se mueven con un desplazamiento lento + zoom, como un vuelo de dron.
MONTAGE = [
    ("gaztelugatxe1", 2), ("costa_zumaia", 2),         # "Hay lugares que no se explican."
    ("pasaia", 2), ("zumaia_vert", 1), ("elantxobe", 1),   # "Se viven."
    ("gaztelugatxe_vert", 2), ("getaria_ilun", 2),
]
END_SHOT = "gaztelugatxe_ilun"   # último plano, con el logo
END_START = MONTAGE_START + sum(b for _, b in MONTAGE) * BEAT
END_LEN = 4.0
DURATION = END_START + END_LEN

# Locución: (archivo, segundo en que empieza)
VOICE = [
    ("vo_00.wav", MONTAGE_START + 0.25),   # Hay lugares que no se explican.
    ("vo_01.wav", MONTAGE_START + 2.75),   # Se viven.
    ("vo_02.wav", END_START + 0.6),        # ¿Preparados para descubrir Euskadi?
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


class ClipReader:
    """Lee fotogramas consecutivos de un vídeo (clips/<nombre>.webm), recortados para cubrir w×h."""

    def __init__(self, name, start, w, h):
        self.size = (w, h)
        vf = (f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={w}:{h},eq=contrast=1.04:saturation=1.08")
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start}", "-i", str(CLIPS / f"{name}.webm"),
                                   "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE)
        self.last = None

    def next(self):
        n = self.size[0] * self.size[1] * 3
        buf = self.p.stdout.read(n)
        if len(buf) == n:   # si el clip se acaba, se congela el último fotograma
            self.last = Image.frombuffer("RGB", self.size, buf)
        return self.last


_readers = {}
def cover(name, w, h, t, zoom=0.06, pan=(0.5, 0.5)):
    """Foto: la recorta para cubrir w×h con un zoom lento (t en 0..1).
    Clip de vídeo ("clip:nombre@segundo"): devuelve el siguiente fotograma desde ese segundo."""
    if name.startswith("clip:"):
        clip, start = name[5:].split("@")
        key = (clip, start, w, h)
        if key not in _readers:
            _readers[key] = ClipReader(clip, float(start), w, h)
        return _readers[key].next()
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
F_Q = font("CormorantGaramond_600SemiBold.ttf", 58)

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
    # --- Fase 1: latidos. La foto se ilumina con cada latido sobre fondo casi negro.
    if t < BANDS[0][0]:
        img = cover(INTRO, W, H, t / MUSIC_START * 0.4, pan=(0.5, 0.45))
        glow = 0.0
        for hb in HEARTBEATS:
            for off, amp in ((0.0, 1.0), (0.22, 0.7)):
                x = t - hb - off
                if x >= 0:
                    glow = max(glow, amp * np.exp(-x / 0.25))
        base = 0.15 + 0.85 * ease((t - HEARTBEATS[-1]) / 0.8) if t > HEARTBEATS[-1] else 0.15
        bright = min(1.0, base + 0.55 * glow)
        img = Image.blend(Image.new("RGB", img.size), img, bright)
        # pequeño "golpe" de zoom en cada latido
        z = 1 + 0.025 * glow
        if z > 1.001:
            cw, ch = W / z, H / z
            img = img.resize((W, H), Image.LANCZOS, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        return draw_text(img, [(TEXT_SMALL, F_SMALL, 10)], H * 0.47, ease((t - HEARTBEATS[1]) / 0.5))

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
        for k, (name, beats) in enumerate(MONTAGE):
            d = beats * BEAT
            if t < ts + d:
                u = (t - ts) / d
                side = 1 if k % 2 == 0 else -1   # alterna la dirección del "vuelo"
                return cover(name, W, H, u, zoom=0.06 + 0.03 * beats, pan=(0.5 + side * 0.18 * (u - 0.5), 0.5))
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
    img = draw_text(out.convert("RGB"), [(TEXT_END, F_END, 8)], H * 0.40 + 270, ta)
    qa = ease((t - VOICE[-1][1]) / 0.4)
    return draw_text(img, [(line, F_Q, 6) for line in TEXT_END_Q], H * 0.70, qa)


def mix_audio(with_music):
    """Latidos + (música) + locución. La música baja automáticamente cuando habla la voz."""
    dest = AUDIO / ("mix_musica.wav" if with_music else "mix_tiktok.wav")
    inputs = ["-i", str(AUDIO / "heartbeat.wav")]
    chains = ["[0:a]aresample=44100,aformat=channel_layouts=stereo,volume=1.1[hb]"]
    if with_music:
        inputs += ["-i", str(AUDIO / "music.wav")]
        ms = int(MUSIC_START * 1000)
        chains.append(f"[1:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=0.8[mus]")
    first = len(inputs) // 2
    for k, (f, start) in enumerate(VOICE, start=first):
        inputs += ["-i", str(AUDIO / f)]
        ms = int(start * 1000)
        chains.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
    n = len(VOICE)
    vo = "".join(f"[v{k}]" for k in range(first, first + n))
    vo_fx = (f"{vo}amix=inputs={n}:normalize=0,highpass=f=80,"
             "equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3,volume=1.6")
    chains.append(vo_fx + (",asplit=2[vo][sc]" if with_music else "[vo]"))
    if with_music:
        chains += ["[mus][sc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=500[duck]",
                   "[hb][duck][vo]amix=inputs=3:normalize=0[pre]"]
    else:
        chains.append("[hb][vo]amix=inputs=2:normalize=0[pre]")
    chains.append(f"[pre]alimiter=limit=0.95,apad=whole_dur={DURATION:.3f}[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(chains),
                    "-map", "[out]", "-t", f"{DURATION:.3f}", "-ar", "44100", str(dest)], check=True)
    return dest


def main():
    outdir = ROOT / "output"
    outdir.mkdir(parents=True, exist_ok=True)
    silent = outdir / "_video.mp4"
    n = round(DURATION * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "19",
           "-pix_fmt", "yuv420p", str(silent)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(np.asarray(frame(k / FPS), dtype=np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    for name, with_music in (("basqplan_para_tiktok.mp4", False), ("basqplan_presentacion.mp4", True)):
        audio = mix_audio(with_music)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(audio), "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-t", f"{DURATION:.3f}", "-movflags", "+faststart",
                        str(outdir / name)], check=True)
        print(f"output/{name}  ({DURATION:.1f} s)")
    silent.unlink()


if __name__ == "__main__":
    main()
