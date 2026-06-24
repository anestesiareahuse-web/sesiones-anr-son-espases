#!/usr/bin/env python3
"""
Fetches all videos from a YouTube playlist and generates videos.json.
Usage: python fetch_videos.py
Requires: YOUTUBE_API_KEY env variable (or GitHub secret).
Manual category overrides: edit manual_categories.json
"""

import json, os, re, sys
from datetime import datetime, timezone
from urllib import request, parse, error

API_KEY     = os.environ.get("YOUTUBE_API_KEY", "")
PLAYLIST_ID = "PLPd-bzWNrSHVDwJDIV3VoZOnwnjU3D0EV"
OUTPUT_FILE = "videos.json"
MANUAL_FILE = "manual_categories.json"
API_BASE    = "https://www.googleapis.com/youtube/v3"
MAX_RESULTS = 50

# ── Keyword map ────────────────────────────────────────────────────────────────
CATEGORIES = {
    "pediatria":      ["pediatr","pediátr","neonat","infant","niño","niña","recién nacido","neonatal","pediátrico","cardiópata pediát","pediátric"],
    "toracica":       ["torác","tórax","toraci","lobectom","neumonectom","toracoscop","mediastin","pleural","neumotórax","ventilación protección","resecabilidad","operabilidad torác","cto","esófago","esofag"],
    "cardiaca":       ["cardíac","cardiac","cardiaca","corazón","heart","valvul","valv","bypass","coronar","aorta","cec","extracorpórea","tavi","teer","miocardi","pericardi","arritmia","fibrilación","brugada","cardiópata"],
    "neuro":          ["neuroanest","neurocirugía","cerebral","intracraneal","craneal","cráneo","columna","medular","craneotom","tce","tec","trombectomía","postrombectomía","neurológ"],
    "regional":       ["regional","bloqueo","block","plexo","nervio","epidural","raquídea","intradural","subaracnoid","tap block","pecs","fascial","quadratus","serratus","paravertebral","erector spinae","esp block","interescalén","supraclavicular","infraclavicular","axilar","femoral","ciático","safeno","poplíteo","prilocaína"],
    "dolor":          ["dolor","pain","postoperat","analgesia","analgés","opioide","opioid","fentanilo","morfin","multimodal","pca","gabapentin","pregabalina","tramadol","ketorolaco","dolor agudo","dolor crónico","sufentanilo","dap","lumbalgia","ofa","opioid free"],
    "viaarea":        ["vía aérea","airway","intubación","intubat","laringoscop","mascarilla laríng","supraglót","videolaringoscop","fibroscop","fibroptia","cricotiroid","traqueotom","laringoscopia","vía aérea difícil","extubación","laringoespasmo"],
    "uci":            ["reanimat","uci","uvi","crítico","crítica","intensiv","resucitación","shock séptico","sepsis","ventilación mecánica","ecmo","parada cardíaca","tep","tromboembolismo","angiotensina","oxemia","hipotensión intraoperatoria","surviving sepsis"],
    "farmaco":        ["farmacol","fármaco","drug","propofol","sevoflur","desflur","isofluran","rocuroni","cisatracuri","sugamadex","neostigmin","dexmedetomidin","midazolam","remifentanilo","relajante","bloqueante neuromuscular","reversi","halogenad","tci","nvpo","hipertermia maligna","ketamin","sustancias de abuso","profundidad anestésica","sedline","bioconect"],
    "casos":          ["caso clínico","caso clini","clinical case","presentación de caso","sesión clínica","a propósito de","hipertermia maligna"],
    "gestion":        ["seguridad","gestión","protocolo","checklist","error","incidente","calidad","simulación","formación","crisis","comunicación","trabajo en equipo","pbm","hemorragia masiva","recuperación intensificada","sensar","dynamed","novedades en anestesia","grupos de trabajo","comisiones","medioambiental","idisba","investigación","desfibrilador","bioconect","hipotermia perioperatoria"],
    "obstetricia":    ["obstetric","obstétric","embarazad","cesárea","parto","matern","perinatal","prenatal","placenta","eclampsia","preeclampsia"],
    "anafilaxia":     ["anafilaxia","anafiláctico","alérgico periop","reacción alérgica"],
    "anciano":        ["anciano","geriátr","fragilidad","frágil","prefrágiil","prefrágil","mayor","envejecim"],
    "cirugia_general":["cirugía general","cirugia general","hipec","atresia","esofag","colect","laparoscop","laparotom","cirugía abdominal"],
    "ecmo":           ["ecmo","oxigenación por membrana"],
    "ecografia":      ["ecograf","pocus","ecoguiad","ultrasonid","ecointens","ecocardiograf"],
    "endocrino":      ["endocrin","tiroides","suprarren","feocromocitoma","diabetes","diabétic","insulina","glp","glp-1","obesidad mórbida","metabolis","hormonal"],
    "fluidoterapia":  ["fluidoter","fluidotherap","cristaloid","coloide","volumen","reposición hídrica"],
    "hematologia":    ["hematolog","coagulación","rotem","teg","tromboelastom","transfus","plaqueta","hemostasia","anticoagul","trombosis","pbm patient blood","pbm"],
    "hemodinamica":   ["hemodinámica","hemodinam","gasto cardíaco","precarga","poscarga","vasopres","noradren","dopamin","control hemodinámico","hipotensión"],
    "hepatico":       ["hepátic","hígado","cirrótico","cirrosis","trasplante hepático","hepat"],
    "infecciosas":    ["infeccios","antibiótic","antibiótico","antimicrob","sepsis infec","multirresistente","multiresistente","ceftazidima","avibactam","carbapenem","infección"],
    "monitorizacion": ["monitorizac","monitoriz","sedline","bis ","entropía","profundidad anestésica","bispectral","pam ","presión arterial invasiva"],
    "nefrologia":     ["nefrol","renal","riñón","insuficiencia renal","diálisis","creatinina","fallo renal","lesión renal aguda","lra","ira"],
    "neurologia":     ["neurolog","ictus","aine cerebrovascular","epilepsia","convuls","parkinson","esclerosis"],
    "obesidad":       ["obesidad","obeso","bariátric","bypass gástrico","manga gástrica","imc elevado"],
    "politrauma":     ["politraum","trauma grave","trauma múltiple","damage control","control de daños"],
    "preoperatorio":  ["preoperator","preoperatori","valoración preoper","visita preanestés","preanestés","ayuno","optimización preop","criterios derivación","glp-1 preop","agonistas glp","autoinmun","enfermedades autoinmunes","hipotermia perioper"],
    "rcp":            ["rcp","reanimación cardiopulmonar","svb","svav","bls","acls","parada cardiorrespiratoria","soporte vital"],
    "trasplante":     ["trasplante","transplante","donante","órgano","injerto"],
    "traumatologia":  ["traumatol","ortopéd","fractura","artroplastia","prótesis","rodilla","cadera"],
    "vascular":       ["vascular","vascula","carótida","aorta abdominal","aneurisma","endovascular","bypass periférico"],
    "ventilacion":    ["ventilación mecánica","ventilación protectora","modo ventilatorio","asincronía","presión soporte","peep","reclutamiento alveolar","weaning","destete","oxigenoterapia","oxemia"],
}


def categorise(title: str) -> list[str]:
    t = title.lower()
    found = [cid for cid, kws in CATEGORIES.items() if any(kw in t for kw in kws)]
    return found if found else ["uncategorised"]


def parse_duration(iso: str) -> str:
    if not iso:
        return ""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return ""
    h, mn, s = int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)
    return f"{h}:{mn:02d}:{s:02d}" if h else f"{mn}:{s:02d}"


def api_get(endpoint: str, params: dict) -> dict:
    params["key"] = API_KEY
    url = f"{API_BASE}/{endpoint}?" + parse.urlencode(params)
    try:
        with request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def load_manual_overrides() -> dict:
    if not os.path.exists(MANUAL_FILE):
        return {}
    with open(MANUAL_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("overrides", {})


def fetch_playlist_videos() -> list[dict]:
    videos, page_token, page = [], None, 1
    overrides = load_manual_overrides()

    while True:
        print(f"  Fetching playlist page {page}…")
        params = {"part": "snippet", "playlistId": PLAYLIST_ID, "maxResults": MAX_RESULTS}
        if page_token:
            params["pageToken"] = page_token

        data = api_get("playlistItems", params)
        items = data.get("items", [])

        video_ids = [
            it["snippet"]["resourceId"]["videoId"]
            for it in items
            if it["snippet"].get("resourceId", {}).get("kind") == "youtube#video"
        ]

        durations = {}
        if video_ids:
            det = api_get("videos", {"part": "contentDetails", "id": ",".join(video_ids)})
            for item in det.get("items", []):
                durations[item["id"]] = parse_duration(item["contentDetails"].get("duration", ""))

        for it in items:
            sn = it["snippet"]
            vid = sn.get("resourceId", {}).get("videoId", "")
            if not vid:
                continue
            title = sn.get("title", "").strip()
            if title in ("Deleted video", "Private video"):
                continue

            # Manual override takes priority; fallback to keyword detection
            cats = overrides.get(vid) or categorise(title)

            videos.append({
                "videoId": vid,
                "title": title,
                "publishedAt": sn.get("publishedAt", ""),
                "duration": durations.get(vid, ""),
                "categories": cats,
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        page += 1

    return videos


def main():
    if not API_KEY:
        print("ERROR: YOUTUBE_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching playlist: {PLAYLIST_ID}")
    videos = fetch_playlist_videos()

    uncat = sum(1 for v in videos if v["categories"] == ["uncategorised"])
    print(f"  → {len(videos)} videos  |  {len(videos)-uncat} clasificados  |  {uncat} sin clasificar")

    existing = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)

    payload = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "playlistId": PLAYLIST_ID,
        "videoCount": len(videos),
        "videos": videos,
    }

    if existing.get("videos") == videos:
        print("No changes detected — videos.json is up to date.")
        gh_out = os.environ.get("GITHUB_OUTPUT")
        if gh_out:
            open(gh_out, "a").write("changed=false\n")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {OUTPUT_FILE}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        open(gh_out, "a").write("changed=true\n")


if __name__ == "__main__":
    main()
