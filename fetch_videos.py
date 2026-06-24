#!/usr/bin/env python3
"""
Fetches all videos from a YouTube playlist and generates videos.json.
Usage: python fetch_videos.py
Requires: YOUTUBE_API_KEY env variable (or edit API_KEY below for local use).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib import request, parse, error

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY      = os.environ.get("YOUTUBE_API_KEY", "")   # set via env or GitHub secret
PLAYLIST_ID  = "PLPd-bzWNrSHVDwJDIV3VoZOnwnjU3D0EV"
OUTPUT_FILE  = "videos.json"
API_BASE     = "https://www.googleapis.com/youtube/v3"
MAX_RESULTS  = 50  # max allowed by API per page

# ── Category keyword map ───────────────────────────────────────────────────────
CATEGORIES = {
    "pediatria": [
        "pediatr","pediátr","neonat","infant","niño","niña",
        "recién nacido","neonatal","pediátrico",
    ],
    "toracica": [
        "torác","tórax","toraci","pulmon","lobectom","neumonectom",
        "toracoscop","mediastin","pleural","neumotórax","pleurodesis","pulmón",
    ],
    "cardiaca": [
        "cardíac","cardiac","cardiaca","corazón","heart","valvul","valv",
        "bypass","coronar","aorta","cec","extracorpórea","tavi","teer",
        "miocardi","pericardi","arritmia","fibrilación",
    ],
    "neuro": [
        "neuroanest","neurocirugía","neuroquirúrg","cerebral","intracraneal",
        "craneal","cráneo","columna","espinal","medular","raquídeo",
        "neuro","craneotom",
    ],
    "regional": [
        "regional","bloqueo","block","plexo","nervio","epidural",
        "raquídea","intradural","subaracnoid","tap block","pecs","fascial",
        "infiltración","haql","quadratus","serratus","paravertebral",
        "erector spinae","esp block","truncal","interescalén",
        "supraclavicular","infraclavicular","axilar","femoral","ciático",
        "safeno","poplíteo","tobillo",
    ],
    "dolor": [
        "dolor","pain","postoperat","analgesia","analgés","opioide","opioid",
        "fentanilo","morfin","ketamin","multimodal","pca","antiinflamator",
        "gabapentin","pregabalina","tramadol","ketorolaco","paracetamol",
        "dolor agudo","dolor crónico",
    ],
    "viaarea": [
        "vía aérea","airway","intubación","intubat","laringoscop",
        "mascarilla laríng","supraglót","videolaringoscop","fibroscop",
        "fibroptia","cricotiroid","traqueotom","traqueostom","laringoscopia",
        "difficult airway","vía aérea difícil","extubación",
    ],
    "uci": [
        "reanimat","uci","uvi","crítico","crítica","intensiv","resucitación",
        "shock","sepsis","ventilación mecánica","rcp","ecmo",
        "hemostasia","hemostatic","daño controlado","politraumat","trauma",
        "emergencia","urgencia","parada cardíaca",
    ],
    "farmaco": [
        "farmacol","fármaco","drug","propofol","sevoflur","desflur",
        "isofluran","desfluran","rocuroni","cisatracuri","sugamadex",
        "neostigmin","dexmedetomidin","midazolam","remifentanilo",
        "sufentanilo","alfentanilo","relajante","bloqueante neuromuscular",
        "reversi","halogenad",
    ],
    "casos": [
        "caso clínico","caso clini","clinical case","presentación de caso",
        "sesión clínica","a propósito de","un caso de","manejo de un",
    ],
    "gestion": [
        "seguridad","gestión","protocolo","checklist","error","incidente",
        "calidad","simulación","simulacro","formación","crisis",
        "comunicación","trabajo en equipo","cultura","burnout",
        "resiliencia","docencia","aprendizaje","evaluación",
    ],
    "obstetricia": [
        "obstetric","obstétric","embarazad","cesárea","parto","matern",
        "perinatal","prenatal","placenta","hemorragia obstétric",
        "uterotónic","eclampsia","preeclampsia",
    ],
}


def categorise(title: str) -> list[str]:
    t = title.lower()
    found = [cid for cid, kws in CATEGORIES.items() if any(kw in t for kw in kws)]
    return found if found else ["uncategorised"]


def parse_duration(iso: str) -> str:
    """Convert ISO 8601 duration (PT1H2M3S) to HH:MM:SS or MM:SS."""
    if not iso:
        return ""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return ""
    h, mn, s = int(m.group(1) or 0), int(m.group(2) or 0), int(m.group(3) or 0)
    if h:
        return f"{h}:{mn:02d}:{s:02d}"
    return f"{mn}:{s:02d}"


def api_get(endpoint: str, params: dict) -> dict:
    params["key"] = API_KEY
    url = f"{API_BASE}/{endpoint}?" + parse.urlencode(params)
    try:
        with request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def fetch_playlist_videos() -> list[dict]:
    videos = []
    page_token = None
    page = 1

    while True:
        print(f"  Fetching playlist page {page}…")
        params = {
            "part": "snippet",
            "playlistId": PLAYLIST_ID,
            "maxResults": MAX_RESULTS,
        }
        if page_token:
            params["pageToken"] = page_token

        data = api_get("playlistItems", params)
        items = data.get("items", [])

        # Collect video IDs for a batch details call
        video_ids = [
            it["snippet"]["resourceId"]["videoId"]
            for it in items
            if it["snippet"].get("resourceId", {}).get("kind") == "youtube#video"
        ]

        # Fetch durations in batch
        durations = {}
        if video_ids:
            det = api_get("videos", {
                "part": "contentDetails",
                "id": ",".join(video_ids),
            })
            for item in det.get("items", []):
                durations[item["id"]] = parse_duration(
                    item["contentDetails"].get("duration", "")
                )

        for it in items:
            sn = it["snippet"]
            vid = sn.get("resourceId", {}).get("videoId", "")
            if not vid:
                continue
            title = sn.get("title", "").strip()
            if title in ("Deleted video", "Private video"):
                continue
            pub = sn.get("publishedAt", "")
            videos.append({
                "videoId": vid,
                "title": title,
                "publishedAt": pub,
                "duration": durations.get(vid, ""),
                "categories": categorise(title),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        page += 1

    return videos


def main():
    if not API_KEY:
        print("ERROR: YOUTUBE_API_KEY is not set.", file=sys.stderr)
        print("Export it first:  export YOUTUBE_API_KEY='AIza...'", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching playlist: {PLAYLIST_ID}")
    videos = fetch_playlist_videos()
    print(f"  → {len(videos)} videos found")

    # Check for changes vs existing file
    existing = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)

    payload = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "playlistId": PLAYLIST_ID,
        "videoCount": len(videos),
        "videos": videos,
    }

    if existing.get("videos") == videos:
        print("No changes detected — videos.json is already up to date.")
        # GitHub Actions: set output so the workflow skips the commit step
        gh_out = os.environ.get("GITHUB_OUTPUT")
        if gh_out:
            with open(gh_out, "a") as f:
                f.write("changed=false\n")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved {OUTPUT_FILE} ({len(videos)} videos)")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write("changed=true\n")


if __name__ == "__main__":
    main()
