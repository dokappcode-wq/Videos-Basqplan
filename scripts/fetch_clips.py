"""Descarga vídeos de Wikimedia Commons (versión transcodificada ~1080p) y guarda créditos.
Uso: python3 scripts/fetch_clips.py clips/list.txt   (formato: nombre_local|File:Titulo.webm)"""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
# Wikimedia pide un User-Agent con contacto: pásalo en WIKIMEDIA_UA (no se guarda en el repositorio).
UA = {"User-Agent": os.environ.get("WIKIMEDIA_UA", "VideoMontageBuilder/1.0 (python-urllib)")}


def get(url, tries=6):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = int(e.headers.get("Retry-After") or 60) + 15   # respeta la espera que pide Wikimedia
            print(f"  esperando {wait}s (límite de Wikimedia)", flush=True)
            time.sleep(wait)
    raise RuntimeError("rate limited: " + url)


strip = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
lst = Path(sys.argv[1]); out = lst.parent
cf = out / "credits.json"
credits = json.loads(cf.read_text()) if cf.exists() else {}
todo = {}
for line in lst.read_text().splitlines():
    if line.strip() and not line.startswith("#"):
        name, title = [x.strip() for x in line.split("|", 1)]
        if not (out / f"{name}.webm").exists():
            todo[title] = name
if todo:
    q = urllib.parse.urlencode(dict(action="query", titles="|".join(todo), prop="videoinfo", format="json",
                                    viprop="url|extmetadata|derivatives|size"))
    data = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))["query"]
    norm = {n["to"]: n["from"] for n in data.get("normalized", [])}
    for page in data["pages"].values():
        title = norm.get(page["title"], page["title"])
        vi = page["videoinfo"][0]; m = vi["extmetadata"]; name = todo[title]
        ders = [d for d in vi.get("derivatives", []) if d.get("type", "").startswith("video/webm")]
        def score(d):
            h = min(d.get("width", 0), d.get("height", 0))
            return (h == 1080, h <= 1080, h)
        best = max(ders, key=score) if ders else {"src": vi["url"]}
        try:
            (out / f"{name}.webm").write_bytes(get(best["src"]))
        except Exception as e:
            print("skip", name, e, flush=True); continue
        credits[name] = dict(title=title, page=vi["descriptionurl"],
                             author=strip(m.get("Artist", {}).get("value")),
                             license=m.get("LicenseShortName", {}).get("value"))
        cf.write_text(json.dumps(credits, indent=2, ensure_ascii=False))
        print("ok", name, best.get("width"), best.get("height"), credits[name]["license"], flush=True)
        time.sleep(45)   # pausa larga entre vídeos para no saturar el servidor
