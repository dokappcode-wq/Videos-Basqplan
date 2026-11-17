# Videos Basqplan

Vídeo de presentación de marca de **Basqplan** en formato TikTok/Reels (vertical 1080×1920, 30 fps, ~12,5 s),
con la misma estructura y el mismo ritmo que el vídeo de referencia ([TikTok de @pinsonmap](https://vm.tiktok.com/ZGdXVHxdj/)).

Resultado: [`output/basqplan_presentacion.mp4`](output/basqplan_presentacion.mp4)

## Estructura

| Tiempo | Qué pasa |
|---|---|
| 0,0 – 1,2 s | Foto a pantalla completa (hayedo de Otzarreta) con "BIENVENIDOS A" en serif pequeño y espaciado |
| 1,2 – 6,3 s | Collage de 3 franjas horizontales: entran deslizando (arriba y abajo) y cambian de foto cada segundo. A los 3,2 s aparece **BASQPLAN** bajo "BIENVENIDOS A" |
| 6,3 – 11,1 s | Montaje rápido a pantalla completa, un plano cada 0,6 s (Gaztelugatxe, Hondarribia, Pasaia, Bilbao, Otzarreta, Urkiola, Getaria…) |
| 11,1 – 12,5 s | Cierre: **BASQPLAN** / PAÍS VASCO |

## Música

El vídeo sale **sin sonido**. La canción del original ("nostalgia") tiene derechos, así que no la incluyo en el archivo.
Al subirlo a TikTok, añade ese sonido (u otro) desde la biblioteca de sonidos de la app, que tiene licencia para usarlos.
Los cortes están pensados para ir a ~100 BPM (un cambio cada 0,6 s).

## Cambiar textos, fotos o tiempos

Todo está al principio de [`scripts/build_video.py`](scripts/build_video.py): `TEXT_SMALL`, `TEXT_BIG`, `TEXT_END`,
la foto de la intro, las franjas (`BANDS`), el montaje (`MONTAGE`) y la duración de cada plano (`SHOT`).
Para usar fotos propias, pon los `.jpg` en `photos/` y escribe su nombre (sin extensión) en el guion.

```bash
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
