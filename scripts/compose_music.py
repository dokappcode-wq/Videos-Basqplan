"""Compone y sintetiza la música del vídeo (original, libre de derechos).

96 BPM, 4/4 (1 compás = 2,5 s). Progresión emotiva Bm – G – D – A.
  compases 0-2  (0.0-7.5 s)   intro: piano en arpegios + cuerdas, crescendo final
  compases 3-8  (7.5-22.5 s)  entra la base: bombo, palmas, hi-hat, bajo y melodía
  compás  9+    (22.5-27 s)   cierre en Re mayor, deja sonar

Uso: python3 scripts/compose_music.py  → audio/music.wav
Requiere: pretty_midi, fluidsynth y el banco de sonidos FluidR3_GM (licencia MIT).
"""
import subprocess
from pathlib import Path
import pretty_midi as pm

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audio"
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

BPM = 96
BEAT = 60 / BPM
BAR = 4 * BEAT

# Acordes: (raíz MIDI del bajo, notas del acorde para piano/cuerdas)
CH = {
    "Bm": (47, [59, 62, 66]),   # B3 D4 F#4
    "G":  (43, [59, 62, 67]),   # B3 D4 G4
    "D":  (50, [57, 62, 66]),   # A3 D4 F#4
    "A":  (45, [57, 61, 64]),   # A3 C#4 E4
}
INTRO = ["G", "D", "A"]
MAIN = ["Bm", "G", "D", "A", "G", "A"]
END = "D"

# Melodía (grado por corchea, None = silencio) para la parte principal; notas en Re mayor.
MELODY = {
    "Bm": [74, None, 73, 74, 76, None, 74, None],
    "G":  [71, None, 74, None, 79, 78, 76, None],
    "D":  [78, None, 76, 74, 73, None, 74, None],
    "A":  [76, None, None, 73, 69, None, 71, 73],
}


def note(inst, pitch, start, dur, vel):
    inst.notes.append(pm.Note(velocity=int(max(1, min(127, vel))), pitch=pitch, start=start, end=start + dur))


def main():
    OUT.mkdir(exist_ok=True)
    mid = pm.PrettyMIDI(initial_tempo=BPM)
    piano = pm.Instrument(program=0, name="piano")
    strings = pm.Instrument(program=49, name="strings")      # slow strings
    pad = pm.Instrument(program=89, name="pad")              # warm pad
    bass = pm.Instrument(program=33, name="bass")
    lead = pm.Instrument(program=46, name="harp")            # arpa pulsada para la melodía
    sweep = pm.Instrument(program=119, name="reverse cymbal")
    drums = pm.Instrument(program=0, is_drum=True, name="drums")

    t = 0.0
    # ---- Intro: arpegios de piano + cuerdas que crecen
    for i, c in enumerate(INTRO):
        root, chord = CH[c]
        arp = chord + [chord[1] + 12, chord[2] + 12, chord[1] + 12, chord[2], chord[1]]
        for k in range(8):
            note(piano, arp[k % len(arp)], t + k * BEAT / 2, BEAT * 1.5, 52 + i * 8 + (8 if k == 0 else 0))
        note(piano, root - 12, t, BAR, 50 + i * 6)
        for p in chord:
            note(strings, p, t, BAR, 38 + i * 14)
        t += BAR
    # barrido de platillo invertido hacia la entrada de la base
    note(sweep, 60, t - 2 * BEAT, 2 * BEAT, 70)

    # ---- Parte principal
    for i, c in enumerate(MAIN):
        root, chord = CH[c]
        # piano: acordes en corcheas sincopadas
        for k, accent in zip(range(8), [1, 0, 0, 1, 0, 0, 1, 0]):
            for p in chord:
                note(piano, p, t + k * BEAT / 2, BEAT / 2 * 0.9, 58 + 16 * accent)
        for p in chord:
            note(pad, p - 12, t, BAR, 50)
            note(strings, p + 12, t, BAR, 50)
        # bajo: corcheas con la raíz
        for k in range(8):
            note(bass, root - 12 + (12 if k in (3, 7) else 0), t + k * BEAT / 2, BEAT / 2 * 0.85, 92 if k % 2 == 0 else 74)
        # melodía
        for k, p in enumerate(MELODY[c]):
            if p is not None:
                note(lead, p, t + k * BEAT / 2, BEAT, 84)
        # batería
        for b in range(4):
            note(drums, 36, t + b * BEAT, 0.1, 100 if b in (0, 2) else 80)          # bombo a negras
            if b in (1, 3):
                note(drums, 39, t + b * BEAT, 0.1, 70)                              # palmas
                note(drums, 38, t + b * BEAT, 0.1, 45)
            note(drums, 42, t + b * BEAT + BEAT / 2, 0.05, 58)                      # hi-hat a contratiempo
        if i == len(MAIN) - 1:  # redoble final
            for k in range(4):
                note(drums, 38, t + 3 * BEAT + k * BEAT / 4, 0.05, 60 + k * 12)
        t += BAR

    # ---- Cierre en Re mayor
    root, chord = CH[END]
    note(drums, 49, t, 2.0, 80)                         # platillo crash
    note(bass, root - 12, t, BAR * 1.6, 90)
    for p in chord + [chord[1] + 12, chord[2] + 12]:
        note(piano, p, t, BAR * 1.6, 70)
        note(strings, p, t, BAR * 1.8, 62)
    for k, p in enumerate([74, 78, 81, 86]):            # arpegio final en arpa
        note(lead, p, t + k * BEAT / 2, BEAT * 3, 72)

    mid.instruments += [piano, strings, pad, bass, lead, sweep, drums]
    midi_path = OUT / "music.mid"
    mid.write(str(midi_path))
    raw = OUT / "music_raw.wav"
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", "44100",
                    "-o", "synth.reverb.active=1", "-o", "synth.reverb.room-size=0.75",
                    "-o", "synth.reverb.level=0.6", "-o", "synth.chorus.active=1",
                    "-F", str(raw), SF2, str(midi_path)], check=True, capture_output=True)
    # normaliza y añade un fundido de salida
    total = t + BAR * 1.8
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-t", f"{total:.2f}",
                    "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={total - 1.6:.2f}:d=1.6",
                    "-ar", "44100", str(OUT / "music.wav")], check=True)
    raw.unlink()
    print(f"audio/music.wav ({total:.2f} s)")


if __name__ == "__main__":
    main()
