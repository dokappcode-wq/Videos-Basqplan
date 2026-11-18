"""Genera la escaleta (reel/escaleta.csv) y el storyboard visual (reel/storyboard.jpg) a partir de SHOTS.
Uso: python3 reel/scripts/make_storyboard.py   (después de build_reel.py)
"""
import csv, io, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_reel as b  # noqa: E402

DESC = {
    "v@19.6": "Aéreo cenital: el mar rompe contra el Flysch", "aereo_bakio": "Bakio y Gaztelugatxe desde el aire",
    "v@45.4": "Detalle: rocas del Flysch y agua", "v@52.6": "Aéreo del Flysch", "k5-ceramica_L": "Colinas verdes de Pagoeta", "anboto": "Monte Anboto", "zumaia_vert": "Playa de Itzurun, Zumaia",
    "gaztelugatxe1": "San Juan de Gaztelugatxe", "anchoas-gaintza-getaria_L": "Puerto de Getaria",
    "pagoeta-txakoli_R": "Viñedos frente al mar", "elantxobe": "Elantxobe, pueblo marinero",
    "v@80.0": "El Flysch desde el mar", "v@54.4": "Aéreo: acantilados del Flysch",
    "granja-barco-flysch_L": "Granja: vaca mirando a cámara", "pagoeta-txakoli_L": "Caserío",
    "otzarreta_vert": "Hayedo de Otzarreta", "urkiola_caballos": "Caballos en Urkiola",
    "aereo_urola": "Costa del Urola desde el aire", "pagoeta-anchoas-getaria_R": "Obrador: preparando anchoas",
    "getaria_ilun": "Getaria al anochecer", "ceramica-barco-flysch_L": "Manos pintando cerámica",
    "ceramica-ganeta_L": "Ceramista trabajando", "gaintza-barco-flysch_L": "Artesano cestero",
    "v@57.8": "Persona contemplando el mar", "pasaia": "Pasai Donibane", "guggenheim_vert": "Bilbao",
    "barco-flysch-gaintza_L": "El Flysch desde el agua", "urkiola_cruces": "Urkiola",
    "costa_zumaia": "Costa de Zumaia", "gaztelugatxe_vert": "Gaztelugatxe",
    "anchoas-gaintza-getaria_R": "Viñedos dorados", "v@62.8": "Aéreo: mar abierto y cabo",
    "v@68.3": "Aéreo: Flysch", "v@77.6": "Rocas del Flysch y oleaje", "v@0.6": "Aéreo cenital del Flysch",
    "v@21.5": "Aéreo cenital: oleaje", "v@43.9": "Rasa mareal del Flysch", "v@31.0": "Aéreo del Flysch",
    "v@15.8": "Costa verde", "v@55.6": "Acantilados del Flysch",
}


def tc(s):
    return f"00:{int(s):02d}.{int(round((s - int(s)) * 100)):02d}"


def source(src):
    if src.startswith("v@"):
        return f"vídeo de la web (portada.mp4) desde {src[2:]} s"
    if (b.ASSETS / f"{src}.jpg").exists():
        return f"foto de basqplan.com · reel/assets/{src}.jpg"
    return f"Wikimedia Commons · photos/{src}.jpg"


def main():
    rows = [("00:00.00", "00:03.33", "Negro", "—", "Latido + «Vivir en Euskadi suena así...» letra a letra", "fundido", "3.33")]
    for i, (t0, src, o) in enumerate(b.SHOTS):
        t1 = b.SHOTS[i + 1][0] if i + 1 < len(b.SHOTS) else b.END_START
        lab = o.get("label")
        text = (f"{lab[0]}{' · ' + lab[1] if lab[1] else ''}" if lab
                else ("logotipo + basqplan" if o.get("brand") else ""))
        rows.append((tc(t0), tc(t1), DESC.get(src, src), source(src), text, o.get("tr", "corte"), f"{t1 - t0:.2f}"))
    rows.append(("00:26.00", "00:30.00", "Cierre sobre navy #101825", "logotipo oficial para fondo oscuro",
                 "basqplan · Dos experiencias. Un plan único. · ¿Preparados para descubrir Euskadi? (desde 27,3 s)",
                 "fundido a navy", "4.00"))
    with open(b.REEL / "escaleta.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["entrada", "salida", "plano", "fuente", "texto en pantalla", "transición", "duración (s)"])
        w.writerows(rows)

    video = b.OUT / "basqplan_reel_musica_temporal.mp4"
    def mid(r):
        a, z = (float(x.split(":")[1]) for x in r[:2])
        return (a + z) / 2
    times = [1.6] + [mid(r) for r in rows[1:-1]] + [29.0]
    TW, TH, cols = 216, 384, 8
    sheet = Image.new("RGB", (cols * TW, ((len(rows) + cols - 1) // cols) * (TH + 40)), b.NAVY)
    d = ImageDraw.Draw(sheet)
    fnt = ImageFont.truetype(str(b.FONTS / "SpaceGrotesk_500Medium.ttf"), 15)
    for k, (t, r) in enumerate(zip(times, rows)):
        png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(video), "-frames:v", "1",
                              "-vf", f"scale={TW}:{TH}", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        x, y = (k % cols) * TW, (k // cols) * (TH + 40)
        sheet.paste(Image.open(io.BytesIO(png)), (x, y))
        d.text((x + 4, y + TH + 3), f"{k:02d}  {r[0]}", font=fnt, fill=b.GOLD)
        d.text((x + 4, y + TH + 20), r[2][:26], font=fnt, fill=b.CREAM)
    sheet.save(b.REEL / "storyboard.jpg", quality=90)
    print("reel/escaleta.csv, reel/storyboard.jpg")


if __name__ == "__main__":
    main()
