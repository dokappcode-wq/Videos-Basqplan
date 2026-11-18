"""Versión corta del Reel de BASQPLAN (15 s, 1080×1920): solo los mejores planos.

Mismo lenguaje que la versión de 30 s: latido sobre negro, «Vivir en Euskadi suena así...»,
imágenes estáticas con cortes secos que se aceleran, y cierre con el logotipo.
Música: pista temporal original (sustituir por «Pathos» — Ludovico Einaudi & Robert Ames, con licencia).
Puntos de sincronía de la música:
  00:00.00  latido · 00:01.33 primera nota · 00:09.33 cortes rápidos (clímax) · 00:12.00 cierre y logotipo

Uso: python3 reel/scripts/build_reel_15.py
     → reel/output/basqplan_reel_15s_musica_temporal.mp4 y basqplan_reel_15s_sin_musica.mp4
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pretty_midi as pm  # noqa: E402
import build_reel as R  # noqa: E402
import importlib.util  # noqa: E402
# se carga por ruta: hay otro compose_music.py (el de los vídeos anteriores) en scripts/
_spec = importlib.util.spec_from_file_location("reel_compose_music", Path(__file__).resolve().parent / "compose_music.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

MUSIC_START = 1.33
BEAT, BAR = M.BEAT, M.BAR

SHOTS = [
    (2.00, "v@19.6", dict(tr="fade")),     # el mar rompe contra el Flysch (cenital)
    (3.33, "aereo_bakio", dict()),         # Bakio y Gaztelugatxe desde el aire
    (4.00, "gaztelugatxe1", dict()),       # San Juan de Gaztelugatxe
    (4.67, "v@52.6", dict()),              # acantilados del Flysch
    (5.33, "elantxobe", dict()),           # Elantxobe
    (6.00, "otzarreta_vert", dict()),      # hayedo de Otzarreta
    (6.67, "aereo_urola", dict()),         # costa del Urola desde el aire
    (7.33, "v@57.8", dict()),              # alguien contemplando el mar
    (8.00, "ceramica-barco-flysch_L", dict()),   # manos en el taller de cerámica
    (8.67, "pagoeta-txakoli_R", dict()),   # viñedos frente al mar
    # clímax: cortes a medio tiempo
    (9.33, "v@68.3", dict()),
    (9.67, "gaztelugatxe_vert", dict()),
    (10.00, "v@0.6", dict()),
    (10.33, "pasaia", dict()),
    (10.67, "v@21.5", dict()),
    (11.00, "zumaia_vert", dict()),
    (11.33, "v@31.0", dict()),
    (11.67, "v@55.6", dict()),
]
END_START = 12.0
DURATION = 15.0
HEARTBEATS = [(0.20, 1.0), (0.95, 0.9)]


def compose():
    """Pista temporal de 15 s: piano (compás 0) → cuerdas (1) → crecida con redoble (2) → clímax (3) → cierre."""
    n = M.n
    mid = pm.PrettyMIDI(initial_tempo=M.BPM)
    piano, strings, slow = pm.Instrument(0), pm.Instrument(48), pm.Instrument(49)
    cello, contra, timp = pm.Instrument(42), pm.Instrument(43), pm.Instrument(47)
    drums = pm.Instrument(0, is_drum=True)
    prog = ["Am", "F", "G", "F"]
    t = MUSIC_START
    for i, c in enumerate(prog):
        root, chord = M.CHORDS[c]
        lvl = i / 3
        n(piano, root - 12, t, BAR, 55 + 30 * lvl)
        step = BEAT / 2 if i < 2 else BEAT / 4
        arp = [root, chord[0], chord[1], chord[2], chord[1] + 12, chord[2], chord[1], chord[0]]
        k = 0
        while k * step < BAR - 1e-6:
            n(piano, arp[k % 8], t + k * step, step * 1.6, 44 + 34 * lvl + (10 if k % 4 == 0 else 0))
            k += 1
        for beat, p, d in M.MOTIF.get(c, M.MOTIF["Am"]):
            n(piano, p, t + beat * BEAT, d * BEAT, 62 + 28 * lvl)
            if i >= 2:
                n(strings, p, t + beat * BEAT, d * BEAT, 80 + 25 * lvl)
                n(strings, p - 12, t + beat * BEAT, d * BEAT, 70 + 25 * lvl)
        if i >= 1:
            for p in chord:
                n(slow, p, t, BAR, 55 + 50 * lvl)
            n(cello, root, t, BAR * 0.95, 65 + 40 * lvl)
            n(contra, root - 12, t, BAR, 50 + 45 * lvl)
        if i >= 2:
            for b in ([0, 2] if i == 2 else [0, 1, 2, 3]):
                n(timp, root - 12 if root - 12 >= 33 else root, t + b * BEAT, BEAT, 70 + 40 * lvl)
        if i == 2:   # redoble hacia el clímax
            for k in range(8):
                n(timp, 45, t + 2 * BEAT + k * BEAT / 4, BEAT / 4, 70 + k * 7)
        if i == 3:   # clímax
            n(drums, 49, t, 2.0, 105)
            for p in [53, 65, 69, 72, 77]:
                n(slow, p, t, BAR, 105)
        t += BAR
    # cierre en Do mayor (12.0 → 15)
    root, chord = M.CHORDS["C"]
    n(contra, root - 12, t, 3.2, 85)
    n(cello, root, t, 3.2, 80)
    n(timp, 36, t, 2.0, 100)
    n(drums, 49, t, 2.5, 85)
    for p in chord + [chord[0] + 12, chord[2] + 12]:
        n(slow, p, t, 3.3, 85)
        n(piano, p, t, 3.2, 72)
    for k, p in enumerate([72, 76, 79, 84]):
        n(piano, p, t + 0.2 + k * 0.18, 2.8, 62 - k * 4)
    n(piano, 88, 12.8, 2.2, 58)
    mid.instruments += [piano, strings, slow, cello, contra, timp, drums]
    return mid


def main():
    M.render(compose(), total=DURATION + 0.4, name="music_temp_15s")
    M.heartbeat(total=DURATION + 0.4, beats=HEARTBEATS, name="heartbeat_15s")
    R.SHOTS, R.END_START, R.DURATION = SHOTS, END_START, DURATION
    R.END_FADE = 0.35
    R.Q_TIME = 12.8
    R.TEXT_IN, R.TEXT_STEP, R.TEXT_OUT = 0.30, 0.028, 1.75
    R.OUT_NAME = "basqplan_reel_15s"
    R.HB_FILE, R.MUSIC_FILE = "heartbeat_15s.wav", "music_temp_15s.wav"
    R.MAKE_COVER = False
    R.main()


if __name__ == "__main__":
    main()
