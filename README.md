# Videos Basqplan

Vídeo de presentación de marca de **Basqplan** en formato TikTok/Reels (vertical 1080×1920, 30 fps, 16 s),
inspirado en el vídeo de referencia ([TikTok de @pinsonmap](https://vm.tiktok.com/ZGdXVHxdj/)).

Hay dos versiones en `output/`:

| Archivo | Audio | Para qué |
|---|---|---|
| [`basqplan_para_tiktok.mp4`](output/basqplan_para_tiktok.mp4) | Latidos + voz en off, **sin música** | Publicar en TikTok añadiendo la canción desde la app ("Ordinary" de Alex Warren). Baja el volumen de la canción para que se oiga la voz. |
| [`basqplan_presentacion.mp4`](output/basqplan_presentacion.mp4) | Latidos + música original + voz | Instagram, web, presentaciones… (sin problemas de derechos) |

"Ordinary" tiene derechos de autor y no puede ir dentro del archivo; TikTok sí tiene licencia para usarla desde su biblioteca de sonidos.

## Estructura

| Tiempo | Imagen | Audio |
|---|---|---|
| 0 – 2 s | La foto del hayedo de Otzarreta se ilumina con cada latido; aparece "WELCOME TO" | Dos latidos de corazón |
| 2 – 4,5 s | Collage de 3 franjas que entran a ritmo; aparece **BASQUE COUNTRY** | Entra la música |
| 4,5 – 12 s | Montaje a pantalla completa (Zumaia, Gaztelugatxe, Otzarreta, Elantxobe, Hondarribia, Getaria) | *"Acantilados que se asoman al mar. Bosques que parecen sacados de un cuento. Esto es Euskadi."* |
| 12 – 16 s | Cierre: logo + BASQPLAN + "¿PREPARADOS PARA DESCUBRIR EUSKADI?" | *"¿Preparados para descubrir Euskadi?"* |

## Logo

El logo original está en `brand/logo_bp.svg`. `python3 scripts/logo.py` genera dos PNG con fondo transparente:
`brand/logo_bp.png` (colores originales) y `brand/logo_bp_blanco.png` (azul → blanco, para fondos oscuros).

## Música y voz en off

- **Música:** original, compuesta por código (`scripts/compose_music.py`, 96 BPM, Si menor – Sol – Re – La) y sintetizada con
  FluidSynth y el banco de sonidos FluidR3_GM (licencia MIT). Libre de derechos.
- **Voz en off:** `scripts/voiceover.py` con [Piper TTS](https://github.com/rhasspy/piper), voz `es_ES-davefx-medium` (licencia CC0).
  El modelo (~60 MB) no está en el repositorio; descárgalo en `voice_models/`:

```bash
mkdir -p voice_models && cd voice_models && for f in es_ES-davefx-medium.onnx es_ES-davefx-medium.onnx.json; do curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/$f; done
```

Requisitos extra: `pip install pretty_midi piper-tts` y `apt-get install fluidsynth fluid-soundfont-gm`.

Para cambiar la locución, edita `LINES` en `scripts/voiceover.py` y ejecútalo; los momentos en que entra cada frase
están en `VOICE`, en `scripts/build_video.py`.

## Cambiar textos, fotos o tiempos

Todo está al principio de [`scripts/build_video.py`](scripts/build_video.py): `TEXT_SMALL`, `TEXT_BIG`, `TEXT_END`,
la foto de la intro, las franjas (`BANDS`), el montaje (`MONTAGE`) y la duración de cada plano (`SHOT`).
Para usar fotos propias, pon los `.jpg` en `photos/` y escribe su nombre (sin extensión) en el guion.

```bash
python3 scripts/compose_music.py          # genera audio/music.wav y audio/heartbeat.wav
python3 scripts/voiceover.py              # genera audio/vo_XX.wav
python3 scripts/build_video.py            # genera las dos versiones en output/
python3 scripts/fetch_commons.py photos/list.txt   # vuelve a descargar las fotos de Wikimedia Commons
```

Requisitos: Python 3 con Pillow y NumPy, y ffmpeg.

## Créditos de las fotos

Todas las fotos son de Wikimedia Commons, con licencias CC0, CC BY o CC BY-SA. Autor, licencia y enlace de cada una
en [`photos/credits.json`](photos/credits.json) y en [`CREDITOS.md`](CREDITOS.md). Las fotos CC BY / CC BY-SA
exigen atribución: al publicar, añade en la descripción algo como *"Fotos: Wikimedia Commons (ver créditos)"* o
enlaza a la lista. Si usas fotos propias de Basqplan, esto deja de aplicar.

Tipografías: Cormorant Garamond y Montserrat (SIL Open Font License).
