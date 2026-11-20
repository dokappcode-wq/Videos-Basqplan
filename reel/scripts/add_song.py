"""Añade «Pathos» (Ludovico Einaudi & Robert Ames) a las versiones sin música del Reel.

La entrada orquestal de la canción (segundo 52,40 del tema) cae justo en el clímax del montaje:
  - Reel 30 s: clímax en 0:23,33 → la canción suena desde 0:02,00 (segundo 31,07 del tema)
  - Reel 15 s: clímax en 0:09,33 → la canción suena desde 0:01,33 (segundo 44,40 del tema)
Antes de ese punto solo suena el piano suave; el latido inicial se mantiene.

Uso: python3 reel/scripts/add_song.py ruta/a/Pathos.mp3
     → reel/output/basqplan_reel_pathos.mp4 y basqplan_reel_15s_pathos.mp4

El archivo de la canción NO se guarda en el repositorio. Para publicar en una cuenta de empresa
hace falta licencia comercial (sincronización + master).
"""
import subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output"
SONG_HIT = 52.40          # segundo del tema en el que entra la orquesta

VERSIONS = [
    # (vídeo sin música, salida, entrada de la canción en el vídeo, clímax del montaje, duración)
    ("basqplan_reel_sin_musica.mp4", "basqplan_reel_pathos.mp4", 2.00, 23.33, 30.0),
    ("basqplan_reel_15s_sin_musica.mp4", "basqplan_reel_15s_pathos.mp4", 1.33, 9.33, 15.0),
]


def main(song):
    for src, dst, music_in, climax, dur in VERSIONS:
        start = SONG_HIT - (climax - music_in)      # segundo del tema que suena al entrar la música
        length = dur - music_in
        ms = int(music_in * 1000)
        pre = climax - music_in                       # parte de piano (antes de la entrada orquestal)
        graph = (
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[s1][s2];"
            # piano suave: +9 dB para que se oiga bajo el latido y los primeros planos
            f"[s1]atrim=start={start:.3f}:duration={pre:.3f},asetpts=PTS-STARTPTS,volume=2.8,"
            f"afade=t=in:st=0:d=0.8[pa];"
            # desde la entrada orquestal: volumen original
            f"[s2]atrim=start={SONG_HIT:.3f}:duration={length - pre:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=out:st={length - pre - 1.4:.3f}:d=1.4[pb];"
            f"[pa][pb]concat=n=2:v=0:a=1,adelay={ms}|{ms}[song];"
            f"[0:a]aresample=48000,volume=0.7[hb];"
            f"[hb][song]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"alimiter=limit=0.9,apad=whole_dur={dur}[out]"
        )
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / src), "-i", song,
                        "-filter_complex", graph, "-map", "0:v", "-map", "[out]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-t", f"{dur}", "-movflags", "+faststart",
                        str(OUT / dst)], check=True)
        print(f"reel/output/{dst}  (canción desde {start:.2f} s del tema; la orquesta entra en {climax} s)")


if __name__ == "__main__":
    main(sys.argv[1])
