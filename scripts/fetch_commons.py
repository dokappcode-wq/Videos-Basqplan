"""Descarga fotos de Wikimedia Commons (miniatura de 2000px de alto) y guarda sus créditos.
Uso: python3 scripts/fetch_commons.py photos/list.txt  (formato: nombre_local|File:Titulo.jpg)"""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

THUMB_H = int(os.environ.get("THUMB_H", 2000))
THUMB = f"h{THUMB_H}"
UA = {"User-Agent": "VideoMontageBuilder/1.0 (python-urllib)"}


def get(url):
    for i in range(8):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(15 * (i + 1))
    raise RuntimeError("rate limited: " + url)


strip = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

lst = Path(sys.argv[1])
out = lst.parent
cf = out / "credits.json"
credits = json.loads(cf.read_text()) if cf.exists() else {}

todo = {}
for line in lst.read_text().splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    name, title = [x.strip() for x in line.split("|", 1)]
    if (out / f"{name}.jpg").exists() and credits.get(name, {}).get("thumb") == THUMB:
        continue
    todo[title] = name

# Una sola consulta a la API para todos los títulos (evita el límite de peticiones).
info = {}
if todo:
    q = urllib.parse.urlencode(dict(action="query", titles="|".join(todo), prop="imageinfo", format="json",
                                    iiprop="url|extmetadata", iiurlheight=THUMB_H))
    data = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))["query"]
    norm = {n["to"]: n["from"] for n in data.get("normalized", [])}
    for page in data["pages"].values():
        info[norm.get(page["title"], page["title"])] = page["imageinfo"][0]

for title, name in todo.items():
    ii = info[title]
    m = ii["extmetadata"]
    try:
        (out / f"{name}.jpg").write_bytes(get(ii["thumburl"]))
    except Exception as e:
        print("skip", name, e, flush=True)
        continue
    credits[name] = dict(title=title, page=ii["descriptionurl"], thumb=THUMB,
                         author=strip(m.get("Artist", {}).get("value")),
                         license=m.get("LicenseShortName", {}).get("value"))
    cf.write_text(json.dumps(credits, indent=2, ensure_ascii=False))
    print("ok", name, credits[name]["license"], credits[name]["author"][:40], flush=True)
    time.sleep(3)
