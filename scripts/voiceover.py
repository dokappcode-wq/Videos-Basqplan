"""Genera la locución (voz en off) frase a frase con Piper TTS (voz es_ES davefx, licencia CC0).

Uso: python3 scripts/voiceover.py   → audio/vo_XX.wav + audio/vo_timing.json
"""
import json, subprocess, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "voice_models" / "es_ES-davefx-medium.onnx"
OUT = ROOT / "audio"

# Guion de la locución. Cada frase va en su propio archivo para sincronizarla con las imágenes.
LINES = [
    "Hay lugares que se miran... y lugares que se sienten.",
    "Acantilados que se asoman al mar.",
    "Bosques que parecen sacados de un cuento.",
    "Montañas, pueblos marineros, y atardeceres que no se olvidan.",
    "Esto es Euskadi.",
    "Descúbrelo con Bask plan.",   # escrito así para que la voz pronuncie bien "Basqplan"
]


def main():
    OUT.mkdir(exist_ok=True)
    timing = []
    for i, text in enumerate(LINES):
        wav = OUT / f"vo_{i:02d}.wav"
        subprocess.run(["piper", "-m", str(MODEL), "-f", str(wav), "--length-scale", "1.12",
                        "--noise-scale", "0.6", "--noise-w-scale", "0.7"],
                       input=text.encode(), check=True, capture_output=True)
        with wave.open(str(wav)) as w:
            dur = w.getnframes() / w.getframerate()
        timing.append(dict(file=wav.name, text=text, duration=round(dur, 3)))
        print(f"{dur:5.2f}s  {text}")
    (OUT / "vo_timing.json").write_text(json.dumps(timing, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
