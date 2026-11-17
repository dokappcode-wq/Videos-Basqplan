"""Genera la locución (voz en off) frase a frase con Kokoro TTS (modelo abierto, licencia Apache 2.0).

Voz: em_alex (masculina, castellano). Alternativas: ef_dora (femenina), em_santa.
Uso: python3 scripts/voiceover.py   → audio/vo_XX.wav

El modelo (~310 MB) va en voice_models/kokoro/ (ver README).
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "voice_models" / "kokoro"
OUT = ROOT / "audio"
VOICE = "em_alex"
SPEED = 0.92

# Guion corto: poca voz, que hablen las imágenes.
LINES = [
    "Hay lugares que no se explican.",
    "Se viven.",
    "¿Preparados para descubrir Euskadi?",
]


def voices_file():
    """Kokoro-onnx espera un .npz con los estilos de voz; lo crea a partir de los .bin descargados."""
    npz = MODEL_DIR / "voices_es.npz"
    if not npz.exists():
        vs = {p.stem: np.fromfile(p, dtype=np.float32).reshape(-1, 1, 256) for p in MODEL_DIR.glob("*.bin")}
        np.savez(npz, **vs)
    return npz


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("vo_*.wav"):
        old.unlink()
    tts = Kokoro(str(MODEL_DIR / "model.onnx"), str(voices_file()))
    timing = []
    for i, text in enumerate(LINES):
        samples, sr = tts.create(text, voice=VOICE, speed=SPEED, lang="es")
        # recorta silencios al principio y al final
        idx = np.where(np.abs(samples) > 0.01)[0]
        samples = samples[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.12 * sr)]
        wav = OUT / f"vo_{i:02d}.wav"
        sf.write(wav, samples, sr)
        timing.append(dict(file=wav.name, text=text, duration=round(len(samples) / sr, 3)))
        print(f"{len(samples) / sr:5.2f}s  {text}")
    (OUT / "vo_timing.json").write_text(json.dumps(timing, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
