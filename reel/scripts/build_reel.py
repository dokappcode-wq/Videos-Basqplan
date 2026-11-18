"""Reel promocional de BASQPLAN — «Vivir en Euskadi suena así...»  (vertical 1080×1920, 30 fps, 30 s)

Monta el vídeo plano a plano a partir de:
  - Metraje aéreo de la web de BASQPLAN  (brand/web/assets/video/web/portada.mp4)
  - Fotos de las experiencias reales de la web, separadas en planos (reel/assets/*.jpg; ver prepare_assets.py)
  - Logotipo oficial para fondo oscuro (brand/web/assets/logo/basqplan-symbol-duo.svg), sin modificar
  - Tipografías de la marca: Fraunces y Space Grotesk; colores: navy #101825, dorado #C9A86B, crema #F7F3EC

Salidas (reel/output/):
  basqplan_reel_musica_temporal.mp4   latido + pista temporal (sustituir por la canción con licencia)
  basqplan_reel_sin_musica.mp4        solo latido (para montar encima la canción definitiva)
  basqplan_reel_portada.jpg           portada vertical para Instagram

Uso:  python3 reel/scripts/build_reel.py        (antes: compose_music.py y prepare_assets.py)
"""
import subprocess, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REEL = Path(__file__).resolve().parent.parent
ROOT = REEL.parent
sys.path.insert(0, str(ROOT / "scripts"))
from logo import render_logo  # noqa: E402

ASSETS, AUDIO, OUT = REEL / "assets", REEL / "audio", REEL / "output"
FONTS = ROOT / "fonts"
FOOTAGE = ROOT / "brand/web/assets/video/web/portada.mp4"
LOGO_SVG = ROOT / "brand/web/assets/logo/basqplan-symbol-duo.svg"   # versión oficial para fondo oscuro

W, H, FPS = 1080, 1920, 30
DURATION = 30.0
BEAT = 60 / 90

NAVY = (16, 24, 37)
GOLD = (201, 168, 107)
GOLD_LIGHT = (212, 196, 168)
CREAM = (247, 243, 236)

# ------------------------------------------------------------------ textos
TEXT_OPEN = ["Vivir en Euskadi", "suena así..."]
TAGLINE = "Dos experiencias. Un plan único."
QUESTION = ["¿Preparados para", "descubrir Euskadi?"]

# ------------------------------------------------------------------ escaleta
# (inicio, fuente, opciones). Cada plano dura hasta el inicio del siguiente.
#   fuente: "v@seg" = metraje aéreo desde ese segundo · otro nombre = foto de reel/assets
#   pos: encuadre fijo (x, y) de 0 a 1      tr: cut (por defecto) / fade
#   Las imágenes son estáticas: sin zoom ni movimiento añadido.
SHOTS = [
    # ESCENA 1 — gancho: negro + latido + texto; la imagen entra con la música
    (3.33, "v@19.6", dict(tr="fade")),                       # el mar rompiendo en el Flysch (cenital)
    (4.67, "aereo_bakio", dict()),                           # Bakio y Gaztelugatxe desde el aire
    (5.33, "v@45.4", dict()),                                # detalle: rocas del Flysch y agua (intriga)
    # ESCENA 2 — entra BASQPLAN (6.00–7.33 revelado de marca sobre el Flysch)
    (6.00, "v@52.6", dict(tr="fade")),
    (7.33, "gaztelugatxe1", dict()),                         # San Juan de Gaztelugatxe
    (8.00, "anchoas-gaintza-getaria_L", dict()),             # puerto de Getaria
    (8.67, "pagoeta-txakoli_R", dict()),                     # viñedos frente al mar
    (9.33, "elantxobe", dict()),                             # Elantxobe, pueblo marinero
    # ESCENA 3 — experiencias reales de BASQPLAN (el título solo va sobre sus propias imágenes)
    (10.00, "v@80.0", dict()),
    (11.33, "v@54.4", dict()),
    (12.67, "k5-ceramica_L", dict()),
    (13.67, "pagoeta-txakoli_L", dict()),
    (14.33, "otzarreta_vert", dict()),                       # hayedo de Otzarreta
    (15.00, "anboto", dict()),                               # monte Anboto
    (15.67, "aereo_urola", dict()),                          # costa del Urola desde el aire
    (16.33, "zumaia_vert", dict()),
    (17.00, "getaria_ilun", dict()),                         # Getaria al anochecer
    (17.67, "ceramica-barco-flysch_L", dict()),
    (18.33, "ceramica-ganeta_L", dict()),
    (19.00, "gaintza-barco-flysch_L", dict()),
    (19.67, "v@57.8", dict()),                               # alguien contemplando el mar
    (20.33, "pasaia", dict()),                               # Pasai Donibane
    (20.67, "guggenheim_vert", dict()),                      # Bilbao
    (21.00, "barco-flysch-gaintza_L", dict()),               # Flysch
    (21.33, "urkiola_cruces", dict()),                       # Urkiola
    (21.67, "costa_zumaia", dict()),                         # costa de Zumaia
    (22.00, "gaztelugatxe_vert", dict()),                    # Gaztelugatxe
    (22.33, "anchoas-gaintza-getaria_R", dict()),            # viñedos dorados
    (22.67, "v@62.8", dict()),                               # mar abierto y cabo
    # ESCENA 4 — clímax: lo más espectacular, cortes a medio tiempo
    (23.33, "v@68.3", dict()),
    (23.67, "v@77.6", dict()),
    (24.00, "v@0.6", dict()),
    (24.33, "v@21.5", dict()),
    (24.67, "v@43.9", dict()),
    (25.00, "v@31.0", dict()),
    (25.33, "v@15.8", dict()),
    (25.67, "v@55.6", dict()),
]
END_START = 26.0          # transición al fondo navy de la marca + logotipo
END_FADE = 0.5

# ------------------------------------------------------------------ utilidades
def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


F_OPEN = font("Fraunces_400Regular_Italic.ttf", 84)
F_WORD = font("Fraunces_600SemiBold.ttf", 96)
F_WORD_I = font("Fraunces_500Medium_Italic.ttf", 96)
F_LABEL = font("SpaceGrotesk_500Medium.ttf", 36)
F_PLACE = font("Fraunces_400Regular_Italic.ttf", 46)
F_TAG = font("Fraunces_400Regular_Italic.ttf", 46)
F_Q = font("Fraunces_400Regular.ttf", 100)
F_COVER = font("Fraunces_400Regular_Italic.ttf", 104)

LOGO = render_logo(420, svg=LOGO_SVG)    # colores originales del SVG oficial (crema + dorado)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---- corrección de color: natural y cinematográfica (verdes profundos, azules del Cantábrico)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r2 = ((_xx - W / 2) / (W / 2)) ** 2 * 0.8 + ((_yy - H / 2) / (H / 2)) ** 2 * 0.6
VIGNETTE = (1 - 0.20 * np.clip(_r2, 0, 1.5))[..., None]
_rng = np.random.default_rng(7)


def grade(img):
    a = np.asarray(img, dtype=np.float32) / 255
    lum = (a * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    a = a + 0.10 * (a - a ** 2) * (2 * a - 1) * -1.0       # curva en S suave
    a = 0.5 + (a - 0.5) * 1.06
    a = a + (np.array([-0.012, 0.004, 0.014]) * (1 - lum) ** 2)   # sombras hacia azul/verde
    a = a + (np.array([0.020, 0.008, -0.014]) * lum ** 2)         # luces cálidas
    g = (a * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    a = g + (a - g) * 0.97                                   # saturación contenida
    a = a * VIGNETTE + 0.012                                 # viñeta suave y negros levantados
    a = a + _rng.normal(0, 0.010, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)   # grano fino
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


# ---- fuentes de imagen
_photo_cache = {}
def photo_base(name):
    """Foto ampliada una vez (con enfoque suave) a 1,35× el tamaño de pantalla para poder moverla."""
    if name not in _photo_cache:
        path = ASSETS / f"{name}.jpg"
        im = Image.open(path if path.exists() else ROOT / "photos" / f"{name}.jpg").convert("RGB")
        s = max(W * 1.35 / im.width, H * 1.35 / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        _photo_cache[name] = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    return _photo_cache[name]


class Footage:
    """Lee fotogramas consecutivos del metraje desde un segundo dado, recortados a vertical (1,1× pantalla)."""
    def __init__(self, start):
        self.w, self.h = round(W * 1.1), round(H * 1.1)
        vf = (f"fps={FPS},scale={self.w}:{self.h}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={self.w}:{self.h},unsharp=5:5:0.6")
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start}", "-i", str(FOOTAGE), "-vf", vf,
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)
        self.frames = []

    def at(self, k):
        while len(self.frames) <= k:
            buf = self.p.stdout.read(self.w * self.h * 3)
            if len(buf) < self.w * self.h * 3:
                self.frames.append(self.frames[-1]); continue
            self.frames.append(Image.frombuffer("RGB", (self.w, self.h), buf))
            if len(self.frames) > 4:              # solo se guardan los últimos fotogramas
                self.frames[-5] = None
        return self.frames[k]


_footage = {}


def shot_frame(i, t):
    """Fotograma del plano i en el instante t (con su movimiento de cámara)."""
    t0, src, o = SHOTS[i]
    t1 = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else END_START + END_FADE
    u = (t - t0) / (t1 - t0)
    # imágenes estáticas: encuadre fijo (pos), sin zoom ni desplazamiento
    z = 1.0
    dx, dy = o.get("pos", (0.5, 0.5))
    if src.startswith("v@"):
        key = (i, src)
        if key not in _footage:
            _footage[key] = Footage(float(src[2:]))
        base = _footage[key].at(int(round((t - t0) * FPS)))
    else:
        base = photo_base(src)
    bw, bh = base.size
    # la base cubre M× la pantalla; se recorta una ventana algo menor para tener margen de movimiento
    M, Z0 = (1.1, 1.06) if src.startswith("v@") else (1.35, 1.15)
    cw, ch = W * M / (Z0 * z), H * M / (Z0 * z)
    x0 = (bw - cw) * dx
    y0 = (bh - ch) * dy
    img = base.resize((W, H), Image.BILINEAR if src.startswith("v@") else Image.LANCZOS,
                      box=(x0, y0, x0 + cw, y0 + ch))
    return img


def draw_lines(img, lines, cy, alpha=1.0, gap=16, shadow=0.0, rise=0):
    """lines: [(texto, fuente, color, tracking_px)] centradas en cy."""
    if alpha <= 0:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    hs = [f.getbbox("ÁHgy")[3] - f.getbbox("ÁHgy")[1] for _, f, _, _ in lines]
    y = cy - (sum(hs) + gap * (len(lines) - 1)) / 2 + rise
    for (txt, f, col, tr), h in zip(lines, hs):
        widths = [d.textlength(c, font=f) for c in txt]
        tw = sum(widths) + tr * (len(txt) - 1)
        x = (W - tw) / 2
        for c, cw in zip(txt, widths):
            d.text((x, y - f.getbbox("ÁHgy")[1]), c, font=f, fill=(*col, int(255 * alpha)))
            x += cw + tr
        y += h + gap
    out = img.convert("RGBA")
    if shadow > 0:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * shadow)))
        out.alpha_composite(sh)
    out.alpha_composite(layer)
    return out.convert("RGB")


def draw_wordmark(img, cy, alpha, size_scale=1.0):
    """«basq» + «plan» en cursiva dorada, como en la web."""
    fa, fb = F_WORD, F_WORD_I
    if size_scale != 1.0:
        fa = font("Fraunces_600SemiBold.ttf", int(96 * size_scale))
        fb = font("Fraunces_500Medium_Italic.ttf", int(96 * size_scale))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tr = -0.02 * fa.size
    def width(txt, f):
        return sum(d.textlength(c, font=f) for c in txt) + tr * (len(txt) - 1)
    wa, wb = width("basq", fa), width("plan", fb)
    x = (W - (wa + wb + 0.02 * fa.size)) / 2
    top = cy - fa.size * 0.55
    for txt, f, col in (("basq", fa, CREAM), ("plan", fb, GOLD)):
        for c in txt:
            d.text((x, top), c, font=f, fill=(*col, int(255 * alpha)))
            x += d.textlength(c, font=f) + tr
        x += 0.02 * fa.size
    out = img.convert("RGBA")
    out.alpha_composite(layer)
    return out.convert("RGB")


def paste_logo(img, cy, alpha, scale=1.0):
    lg = LOGO if scale == 1.0 else LOGO.resize((round(LOGO.width * scale), round(LOGO.height * scale)), Image.LANCZOS)
    lg = lg.copy()
    lg.putalpha(lg.getchannel("A").point(lambda v: int(v * alpha)))
    out = img.convert("RGBA")
    out.alpha_composite(lg, ((W - lg.width) // 2, int(cy - lg.height / 2)))
    return out.convert("RGB")


def draw_label(img, title, place, a):
    """Etiqueta de experiencia: línea dorada + título en Space Grotesk + lugar en Fraunces cursiva."""
    if a <= 0:
        return img
    base_y = H * 0.80
    d = ImageDraw.Draw(img, "RGBA")
    lw = int(56 * a)
    d.rectangle((W / 2 - lw / 2, base_y - 70, W / 2 + lw / 2, base_y - 67), fill=(*GOLD, int(255 * a)))
    lines = [(title.upper(), F_LABEL, CREAM, 6)]
    if place:
        lines.append((place, F_PLACE, GOLD_LIGHT, 0))
    return draw_lines(img, lines, base_y, alpha=a, gap=14, shadow=0.75, rise=int(10 * (1 - a)))


# ------------------------------------------------------------------ composición por fotograma
def shot_index(t):
    i = 0
    for k, (t0, _, _) in enumerate(SHOTS):
        if t >= t0:
            i = k
    return i


def frame(t):
    black = Image.new("RGB", (W, H), (6, 8, 12))

    # ---- ESCENA 1a: negro + latido + «Vivir en Euskadi suena así...»
    if t < SHOTS[0][0]:
        img = black
    else:
        i = shot_index(t)
        img = shot_frame(i, t)
        t0, src, o = SHOTS[i]
        if o.get("tr") == "fade" and t - t0 < 0.35:
            prev = black if i == 0 else shot_frame(i - 1, t)
            img = Image.blend(prev, img, ease_io((t - t0) / 0.35))
        img = grade(img)
        # revelado de marca (ESCENA 2)
        if o.get("brand"):
            t1 = SHOTS[i + 1][0]
            k_in, k_out = ease((t - t0 - 0.10) / 0.45), 1 - ease_io((t - (t1 - 0.25)) / 0.25)
            a = max(0.0, min(k_in, k_out))
            img = Image.blend(img, Image.new("RGB", img.size, NAVY), 0.45 * a)
            img = paste_logo(img, H * 0.45, a, scale=0.62 + 0.04 * k_in)
            img = draw_wordmark(img, H * 0.45 + 175, a, size_scale=0.9)
        # etiquetas de experiencias
        lab = o.get("label")
        if lab:
            # la etiqueta aparece al empezar su grupo y se mantiene mientras dure
            g0 = t0
            for k in range(i, -1, -1):
                if SHOTS[k][2].get("label") == lab:
                    g0 = SHOTS[k][0]
                else:
                    break
            g1 = SHOTS[i + 1][0]
            for k in range(i + 1, len(SHOTS)):
                if SHOTS[k][2].get("label") == lab:
                    g1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else END_START
                else:
                    break
            a = min(ease((t - g0 - 0.05) / 0.3), 1 - ease_io((t - (g1 - 0.15)) / 0.15))
            img = draw_label(img, lab[0], lab[1], a)

    # texto inicial: aparece letra a letra, se va cuando entra la imagen
    if t < 3.75:
        a_out = 1 - ease_io((t - 3.05) / 0.5)
        layer_img = img
        lines = TEXT_OPEN
        # alfa por carácter: aparición progresiva
        all_chars = sum(len(l) for l in lines)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        hs = F_OPEN.getbbox("ÁHgy")[3] - F_OPEN.getbbox("ÁHgy")[1]
        y = H * 0.5 - (2 * hs + 22) / 2
        idx = 0
        for line in lines:
            widths = [d.textlength(c, font=F_OPEN) for c in line]
            x = (W - (sum(widths) + 2 * (len(line) - 1))) / 2
            for c, cw in zip(line, widths):
                ta = ease((t - 0.45 - idx * 0.045) / 0.45) * a_out
                rise = 12 * (1 - ease((t - 0.45 - idx * 0.045) / 0.6))
                if ta > 0:
                    d.text((x, y + rise - F_OPEN.getbbox("ÁHgy")[1]), c, font=F_OPEN, fill=(*CREAM, int(255 * ta)))
                x += cw + 2
                idx += 1
            y += hs + 22
        out = layer_img.convert("RGBA")
        out.alpha_composite(layer)
        img = out.convert("RGB")

    # ---- ESCENA 4b: transición elegante al fondo navy y cierre de marca
    if t >= END_START:
        k = ease_io((t - END_START) / END_FADE)
        bg = Image.new("RGB", (W, H), NAVY)
        if k < 1:
            last = len(SHOTS) - 1
            img = Image.blend(grade(shot_frame(last, t)), bg, k)
        else:
            img = bg
        e = t - END_START
        # bloque de marca: logo + nombre + lema, sube un poco cuando entra la pregunta
        lift = -110 * ease_io((t - 27.3) / 0.6)
        img = paste_logo(img, H * 0.36 + lift, ease((e - 0.25) / 0.6), scale=0.80 + 0.04 * ease(e / 1.2))
        img = draw_wordmark(img, H * 0.36 + 215 + lift, ease((e - 0.55) / 0.5), size_scale=0.95)
        img = draw_lines(img, [(TAGLINE, F_TAG, GOLD_LIGHT, 0)], H * 0.36 + 320 + lift, ease((e - 0.9) / 0.5))
        # la pregunta final, con protagonismo
        qa = ease((t - 27.3) / 0.7)
        if qa > 0:
            d = ImageDraw.Draw(img)
            lw = int(70 * qa)
            yl = H * 0.62
            d.rectangle((W / 2 - lw / 2, yl - 1, W / 2 + lw / 2, yl + 1), fill=GOLD)
            img = draw_lines(img, [(q, F_Q, CREAM, 0) for q in QUESTION], H * 0.71, qa, gap=18,
                             rise=int(18 * (1 - qa)))
    return img


# ------------------------------------------------------------------ audio y salida
def mix(with_music, dest):
    ins = ["-i", str(AUDIO / "heartbeat.wav")]
    graph = "[0:a]volume=1.0[hb];"
    if with_music:
        ins += ["-i", str(AUDIO / "music_temp.wav")]
        graph += "[1:a]volume=1.0[mu];[hb][mu]amix=inputs=2:normalize=0[m];"
    else:
        graph += "[hb]anull[m];"
    graph += f"[m]loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.9,apad=whole_dur={DURATION}[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "[out]",
                    "-t", f"{DURATION}", "-ar", "48000", str(dest)], check=True)


def cover():
    """Portada vertical (1080×1920). Contenido importante dentro del recorte 4:5 central del perfil."""
    f = Footage(53.4)
    base = f.at(0)
    cw, ch = base.width / 1.1, base.height / 1.1
    img = base.resize((W, H), Image.LANCZOS, box=((base.width - cw) / 2, (base.height - ch) / 2,
                                                  (base.width + cw) / 2, (base.height + ch) / 2))
    img = grade(img)
    grad = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    shade = 0.15 + 0.45 * np.clip((grad - 0.35) / 0.65, 0, 1)
    a = np.asarray(img, dtype=np.float32) * (1 - shade) + np.array(NAVY, dtype=np.float32) * shade
    img = Image.fromarray(a.astype(np.uint8))
    img = draw_lines(img, [(TEXT_OPEN[0], F_COVER, CREAM, 0), (TEXT_OPEN[1], F_COVER, CREAM, 0)],
                     H * 0.47, gap=20, shadow=0.8)
    img = paste_logo(img, H * 0.70, 1.0, scale=0.42)
    img = draw_wordmark(img, H * 0.70 + 120, 1.0, size_scale=0.62)
    f.p.kill()
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    silent = OUT / "_video.mp4"
    n = round(DURATION * FPS)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", str(silent)], stdin=subprocess.PIPE)
    for k in range(n):
        enc.stdin.write(np.asarray(frame(k / FPS), dtype=np.uint8).tobytes())
        if k % 150 == 0:
            print(f"  {k / FPS:5.1f} s", flush=True)
    enc.stdin.close(); enc.wait()
    for f in _footage.values():
        f.p.kill()
    for name, music in (("basqplan_reel_musica_temporal", True), ("basqplan_reel_sin_musica", False)):
        wav = AUDIO / f"_{name}.wav"
        mix(music, wav)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(wav), "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-t", f"{DURATION}", "-movflags", "+faststart",
                        str(OUT / f"{name}.mp4")], check=True)
        wav.unlink()
        print(f"reel/output/{name}.mp4")
    silent.unlink()
    cover().save(OUT / "basqplan_reel_portada.jpg", quality=95)
    print("reel/output/basqplan_reel_portada.jpg")


if __name__ == "__main__":
    main()
