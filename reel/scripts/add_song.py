"""Añade «Pathos» (Ludovico Einaudi & Robert Ames) a las versiones sin música del Reel.

La canción empieza en el minuto 2:16 del tema justo cuando entra la música en el vídeo
(0:02,00 en el Reel de 30 s y 0:01,33 en el de 15 s), después del latido sobre negro.

Uso: python3 reel/scripts/add_song.py ruta/a/Pathos.mp3 [segundo_de_inicio=136]
     → reel/output/basqplan_reel_pathos.mp4 y basqplan_reel_15s_pathos.mp4

El archivo de la canción NO se guarda en el repositorio. Para publicar en una cuenta de empresa
hace falta licencia comercial (sincronización + master).
"""
import subprocess, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output"
SONG_START = 136.0        # 2:16 del tema

VERSIONS = [
    # (vídeo sin música, salida, entrada de la canción en el vídeo, clímax del montaje, duración)
    ("basqplan_reel_sin_musica.mp4", "basqplan_reel_pathos.mp4", 2.00, 23.33, 30.0),
    ("basqplan_reel_15s_sin_musica.mp4", "basqplan_reel_15s_pathos.mp4", 1.33, 9.33, 15.0),
]


def main(song, song_start=SONG_START):
    for src, dst, music_in, _climax, dur in VERSIONS:
        length = dur - music_in
        ms = int(music_in * 1000)
        graph = (
            f"[1:a]atrim=start={song_start:.3f}:duration={length:.3f},asetpts=PTS-STARTPTS,"
            f"aresample=48000,aformat=channel_layouts=stereo,"
            f"afade=t=in:st=0:d=0.5,afade=t=out:st={length - 1.5:.3f}:d=1.5,adelay={ms}|{ms}[song];"
            f"[0:a]aresample=48000,volume=0.8[hb];"
            f"[hb][song]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"alimiter=limit=0.9,apad=whole_dur={dur}[out]"
        )
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / src), "-i", song,
                        "-filter_complex", graph, "-map", "0:v", "-map", "[out]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "256k", "-t", f"{dur}", "-movflags", "+faststart",
                        str(OUT / dst)], check=True)
        m, sec = divmod(song_start, 60)
        print(f"reel/output/{dst}  (canción desde {int(m)}:{sec:05.2f}, entra en el vídeo en {music_in} s)")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else SONG_START)
