import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

API_KEY = os.environ["YOUTUBE_API_KEY"]
CHANNEL_ID = "UC22QeXqlLbObRMgGRxE_QBw"
UPLOADS_ID = "UU22QeXqlLbObRMgGRxE_QBw"
FILE = Path("videos.json")

def api(resource, **params):
    params["key"] = API_KEY
    url = (
        "https://www.googleapis.com/youtube/v3/"
        + resource + "?"
        + urllib.parse.urlencode(params)
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except Exception:
        raise RuntimeError("YouTube API request failed") from None

old = json.loads(FILE.read_text()) if FILE.exists() else {}
videos = {v["id"]: v for v in old.get("videos", [])}

# Retrieve uploaded videos and completed streams
token = None

while True:
    params = {
        "part": "snippet",
        "playlistId": UPLOADS_ID,
        "maxResults": 50
    }

    if token:
        params["pageToken"] = token

    result = api("playlistItems", **params)

    for item in result.get("items", []):
        s = item["snippet"]
        vid = s["resourceId"]["videoId"]

        if s["title"] in ("Private video", "Deleted video"):
            videos.pop(vid, None)
            continue

        videos[vid] = {
            "id": vid,
            "title": s["title"],
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "publishedAt": s["publishedAt"]
        }

    token = result.get("nextPageToken")

    if not token:
        break

# Detect active livestreams
result = api(
    "search",
    part="snippet",
    channelId=CHANNEL_ID,
    eventType="live",
    type="video",
    maxResults=5
)

live = None

for item in result.get("items", []):
    vid = item["id"]["videoId"]

    live = {
        "id": vid,
        "title": item["snippet"]["title"],
        "url": f"https://www.youtube.com/watch?v={vid}",
        "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    }
    break

output = {
    "channelId": CHANNEL_ID,
    "updatedAt": datetime.now(timezone.utc).isoformat(),
    "isLive": live is not None,
    "live": live,
    "videos": sorted(
        videos.values(),
        key=lambda v: v["publishedAt"],
        reverse=True
    )
}

FILE.write_text(json.dumps(output, indent=2))

print("Videos synced:", len(videos))
print("Live now:", live is not None)
