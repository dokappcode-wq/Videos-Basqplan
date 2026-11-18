"""Prepara los planos fotográficos del Reel a partir de las fotos de la web de BASQPLAN.

Muchas fotos de la web son dípticos (dos imágenes juntas: «dos experiencias, un plan»).
Este script separa cada díptico en dos planos:
  1400×875 → _L / _R (izquierda / derecha)      800×1000 → _T / _B (arriba / abajo)
Uso: python3 reel/scripts/prepare_assets.py   → reel/assets/*.jpg
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
SRC, OUT = ROOT / "brand/web/assets/img", ROOT / "reel/assets"
OUT.mkdir(parents=True, exist_ok=True)
for p in sorted(SRC.glob("*.jpg")):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    if (w, h) == (1400, 875):
        parts = {"L": (0, 0, 700, 875), "R": (700, 0, 1400, 875)}
    elif (w, h) == (800, 1000):
        parts = {"T": (0, 0, 800, 500), "B": (0, 500, 800, 1000)}
    else:
        im.save(OUT / p.name, quality=95)
        continue
    for tag, box in parts.items():
        im.crop(box).save(OUT / f"{p.stem}_{tag}.jpg", quality=95)
print(f"{len(list(OUT.glob('*.jpg')))} planos en reel/assets/")
