"""Busca fotos en Wikimedia Commons y muestra candidatas (url, licencia, autor)."""
import json, sys, time, urllib.error, urllib.parse, urllib.request
UA = {"User-Agent": "VideoMontageBuilder/1.0 (python-urllib)"}
def api(params):
    params.update(format="json")
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(5 * (i + 1))
    raise RuntimeError("rate limited")
for q in sys.argv[1:]:
    r = api(dict(action="query", generator="search", gsrsearch=f"filetype:bitmap {q}", gsrnamespace=6,
                 gsrlimit=8, prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=1400))
    print("==", q, flush=True); time.sleep(2)
    for p in sorted(r.get("query", {}).get("pages", {}).values(), key=lambda p: p["index"]):
        ii = p["imageinfo"][0]; m = ii["extmetadata"]
        lic = m.get("LicenseShortName", {}).get("value", "?")
        print(f'  {ii["width"]}x{ii["height"]} | {lic} | {p["title"]}')
