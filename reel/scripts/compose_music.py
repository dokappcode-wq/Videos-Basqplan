"""Pista musical TEMPORAL (original, neoclásica: piano + cuerdas) y latido de corazón para el Reel.

Se sustituye por la canción definitiva con licencia (referencia: «Pathos», Ludovico Einaudi & Robert Ames).
Puntos de sincronía (ver STORYBOARD.md):
  00:00.00  latido sobre negro (este archivo: heartbeat.wav)
  00:02.00  entra la música (piano solo)
  00:10.00  empieza el bloque de experiencias (la música crece)
  00:23.33  clímax (cortes rápidos)
  00:26.00  resolución + cierre de marca, la música se deja sonar hasta 00:30

90 BPM, 4/4 → 1 tiempo = 0,667 s, 1 compás = 2,667 s. La música empieza en el segundo 2,0.
Progresión: Am – F – C – G (dos vueltas) → F (clímax) → C (cierre).

Uso: python3 reel/scripts/compose_music.py → reel/audio/music_temp.wav, reel/audio/heartbeat.wav
Requiere: pretty_midi, fluidsynth y el banco de sonidos FluidR3_GM (licencia MIT).
"""
import subprocess, wave
from pathlib import Path
import numpy as np
import pretty_midi as pm

REEL = Path(__file__).resolve().parent.parent
OUT = REEL / "audio"
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

BPM = 90
BEAT = 60 / BPM
BAR = 4 * BEAT
MUSIC_START = 2.0
HEARTBEATS = [(0.25, 1.0), (1.05, 0.95), (1.85, 0.6)]   # (segundo, intensidad)

CHORDS = {   # bajo, acorde (mano izquierda / cuerdas)
    "Am": (45, [57, 60, 64]), "F": (41, [57, 60, 65]),
    "C": (48, [55, 60, 64]), "G": (43, [55, 59, 62]),
}
PROG = ["Am", "F", "C", "G", "Am", "F", "C", "G", "F"]   # 9 compases: 2.0 → 26.0
# Motivo de la melodía (original): (tiempo dentro del compás, nota, duración en tiempos)
MOTIF = {
    "Am": [(0, 76, 1.5), (1.5, 72, 0.5), (2, 74, 0.5), (2.5, 76, 1.5)],
    "F":  [(0, 77, 1.5), (1.5, 76, 0.5), (2, 74, 0.5), (2.5, 72, 1.5)],
    "C":  [(0, 76, 1.0), (1, 79, 1.0), (2, 76, 0.5), (2.5, 74, 1.5)],
    "G":  [(0, 74, 1.5), (1.5, 71, 0.5), (2, 72, 0.5), (2.5, 74, 1.5)],
}


def n(inst, pitch, start, dur, vel):
    inst.notes.append(pm.Note(velocity=int(max(1, min(127, vel))), pitch=int(pitch),
                              start=start, end=start + dur))


def compose():
    mid = pm.PrettyMIDI(initial_tempo=BPM)
    piano = pm.Instrument(0, name="piano")
    strings = pm.Instrument(48, name="strings")
    slow = pm.Instrument(49, name="slow strings")
    cello = pm.Instrument(42, name="cello")
    contra = pm.Instrument(43, name="contrabass")
    timp = pm.Instrument(47, name="timpani")
    drums = pm.Instrument(0, is_drum=True, name="perc")

    t = MUSIC_START
    for i, c in enumerate(PROG):
        root, chord = CHORDS[c]
        lvl = i / (len(PROG) - 1)          # 0 → 1: crecimiento continuo
        # piano: notas graves largas al principio, arpegio desde el compás 1, semicorcheas desde el 5
        n(piano, root - 12, t, BAR, 48 + 30 * lvl)
        if i == 0:
            for k, p in enumerate([chord[0], chord[2], chord[1] + 12]):
                n(piano, p, t + k * BEAT * 1.3, BEAT * 2.5, 42)
        else:
            step = BEAT / 2 if i < 5 else BEAT / 4
            arp = [root, chord[0], chord[1], chord[2], chord[1] + 12, chord[2], chord[1], chord[0]]
            k = 0
            while k * step < BAR - 1e-6:
                n(piano, arp[k % len(arp)], t + k * step, step * 1.6, 40 + 34 * lvl + (10 if k % 4 == 0 else 0))
                k += 1
        # melodía (piano mano derecha desde el compás 0; cuerdas agudas la doblan desde el compás 6)
        for beat, p, d in MOTIF.get(c, MOTIF["Am"]):
            n(piano, p, t + beat * BEAT, d * BEAT, 58 + 30 * lvl)
            if i >= 6:
                n(strings, p, t + beat * BEAT, d * BEAT, 70 + 30 * lvl)
                n(strings, p - 12, t + beat * BEAT, d * BEAT, 60 + 30 * lvl)
        # colchón de cuerdas desde el compás 2, chelo desde el 3
        if i >= 2:
            for p in chord:
                n(slow, p, t, BAR, 36 + 60 * lvl)
        if i >= 3:
            n(cello, root, t, BAR * 0.95, 55 + 45 * lvl)
            n(contra, root - 12, t, BAR, 40 + 50 * lvl)
        # pulso de timbal desde el compás 4, más denso hacia el clímax
        if i >= 4:
            hits = [0, 2] if i < 7 else [0, 1, 2, 3]
            for b in hits:
                n(timp, root - 12 if root - 12 >= 33 else root, t + b * BEAT, BEAT, 60 + 50 * lvl)
        if i == 7:   # redoble hacia el clímax
            for k in range(8):
                n(timp, 45, t + 2 * BEAT + k * BEAT / 4, BEAT / 4, 70 + k * 7)
            n(drums, 57, t + BAR - 0.02, 0.1, 1)
        t += BAR

    # clímax en 23.33 ya está dentro del último compás de PROG (F); platillo al entrar
    climax = MUSIC_START + 8 * BAR
    n(drums, 49, climax, 2.0, 105)
    n(drums, 57, climax, 2.0, 80)
    for p in [53, 65, 69, 72, 77]:
        n(slow, p, climax, BAR, 105)

    # cierre en Do mayor (26.0 → 30): acorde que se deja sonar + nota final al aparecer la pregunta
    end = t
    root, chord = CHORDS["C"]
    n(contra, root - 12, end, 4.0, 85)
    n(cello, root, end, 4.0, 80)
    n(timp, 36, end, 2.0, 100)
    n(drums, 49, end, 3.0, 85)
    for p in chord + [chord[0] + 12, chord[2] + 12]:
        n(slow, p, end, 4.2, 85)
        n(piano, p, end, 4.0, 72)
    for k, p in enumerate([72, 76, 79, 84]):
        n(piano, p, end + 0.25 + k * 0.22, 3.5, 62 - k * 4)
    n(piano, 88, 27.2, 2.8, 58)        # «¿Preparados para descubrir Euskadi?»

    mid.instruments += [piano, strings, slow, cello, contra, timp, drums]
    return mid


def render(mid, total=30.4, name="music_temp"):
    OUT.mkdir(parents=True, exist_ok=True)
    midi = OUT / f"{name}.mid"
    mid.write(str(midi))
    raw = OUT / "_raw.wav"
    subprocess.run(["fluidsynth", "-ni", "-g", "0.55", "-r", "48000",
                    "-o", "synth.reverb.active=1", "-o", "synth.reverb.room-size=0.9",
                    "-o", "synth.reverb.width=1.0", "-o", "synth.reverb.level=0.75",
                    "-F", str(raw), SF2, str(midi)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-t", f"{total}",
                    "-af", "highpass=f=30,loudnorm=I=-15:TP=-1.5:LRA=14,"
                           f"afade=t=out:st={total - 1.6}:d=1.6", "-ar", "48000", str(OUT / f"{name}.wav")],
                   check=True)
    raw.unlink()


def heartbeat(total=30.4, sr=48000, beats=None, name="heartbeat"):
    """Latido grave y cinematográfico (lub-dub) sintetizado."""
    t = np.arange(int(sr * total)) / sr
    out = np.zeros_like(t)

    def thump(t0, f, amp, decay):
        x = t - t0
        on = x >= 0
        env = np.where(on, (1 - np.exp(-x / 0.005)) * np.exp(-x / decay), 0.0)
        ph = 2 * np.pi * (f * x - 22 * decay * np.expm1(-x / decay))
        return amp * env * np.sin(np.where(on, ph, 0))

    for t0, a in (beats or HEARTBEATS):
        out += thump(t0, 48, a, 0.11) + thump(t0 + 0.24, 42, 0.68 * a, 0.10)
    # cola de sala muy suave
    tail = np.convolve(out, np.exp(-np.arange(int(0.35 * sr)) / (0.08 * sr)) * 0.0009, mode="full")[: len(out)]
    out = np.tanh((out + tail) * 1.5) * 0.92
    pcm = (np.stack([out, out], 1) * 32767).astype(np.int16)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    render(compose())
    heartbeat()
    print("reel/audio/music_temp.wav, reel/audio/heartbeat.wav")
