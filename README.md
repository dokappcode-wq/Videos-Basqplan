# Videos Basqplan

Vídeo de presentación de marca de **Basqplan** en formato TikTok/Reels (vertical 1080×1920, 30 fps, 27 s, con música y voz en off),
con la misma estructura y el mismo ritmo que el vídeo de referencia ([TikTok de @pinsonmap](https://vm.tiktok.com/ZGdXVHxdj/)).

Resultado: [`output/basqplan_presentacion.mp4`](output/basqplan_presentacion.mp4)

## Estructura

| Tiempo | Imagen | Voz en off |
|---|---|---|
| 0 – 1,25 s | Hayedo de Otzarreta a pantalla completa con "WELCOME TO" | *"Hay lugares que se miran… y lugares que se sienten."* |
| 1,25 – 7,5 s | Collage de 3 franjas que entran y cambian al ritmo; aparece **BASQUE COUNTRY** | — (solo música) |
| 7,5 – 22,5 s | Entra la base de la música: montaje a pantalla completa al ritmo (acantilados, bosque, montaña, pueblos, atardecer, Gaztelugatxe, pintxos, Bilbao…) | *"Acantilados que se asoman al mar. Bosques que parecen sacados de un cuento. Montañas, pueblos marineros, y atardeceres que no se olvidan. Esto es Euskadi."* |
| 22,5 – 27 s | Cierre sobre el atardecer: logo de Basqplan + BASQPLAN / EUSKADI | *"Descúbrelo con Basqplan."* |

La música baja de volumen automáticamente mientras habla la voz.

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
python3 scripts/compose_music.py          # genera audio/music.wav
python3 scripts/voiceover.py              # genera audio/vo_XX.wav
python3 scripts/build_video.py            # genera output/basqplan_presentacion.mp4
python3 scripts/fetch_commons.py photos/list.txt   # vuelve a descargar las fotos de Wikimedia Commons
```

Requisitos: Python 3 con Pillow y NumPy, y ffmpeg.

## Créditos de las fotos

Todas las fotos son de Wikimedia Commons, con licencias CC0, CC BY o CC BY-SA. Autor, licencia y enlace de cada una
en [`photos/credits.json`](photos/credits.json) y en [`CREDITOS.md`](CREDITOS.md). Las fotos CC BY / CC BY-SA
exigen atribución: al publicar, añade en la descripción algo como *"Fotos: Wikimedia Commons (ver créditos)"* o
enlaza a la lista. Si usas fotos propias de Basqplan, esto deja de aplicar.

Tipografías: Cormorant Garamond y Montserrat (SIL Open Font License).
