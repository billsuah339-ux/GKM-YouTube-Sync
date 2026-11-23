
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# God's Kingdom Ministry YouTube channel
CHANNEL_ID = "UC22QeXqlLbObRMgGRxE_QBw"
OUTPUT = Path("videos.json")

FEED_URL = (
    "https://www.youtube.com/feeds/videos.xml"
    f"?channel_id={CHANNEL_ID}"
)

ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/schemas/2015}"


def sync_videos():
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "GKM-YouTube-Sync/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    # Keep videos already discovered on earlier checks.
    existing = {}

    if OUTPUT.exists():
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        for video in data.get("videos", []):
            existing[video["id"]] = video

    for entry in root.findall(f"{ATOM}entry"):
        video_id = entry.findtext(f"{YT}videoId")
        title = entry.findtext(f"{ATOM}title", default="GKM Video")
        published = entry.findtext(f"{ATOM}published", default="")

        if not video_id:
            continue

        existing[video_id] = {
            "id": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "publishedAt": published
        }

    videos = sorted(
        existing.values(),
        key=lambda video: video.get("publishedAt", ""),
        reverse=True
    )

    result = {
        "channelId": CHANNEL_ID,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "videos": videos
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"GKM sync complete: {len(videos)} videos saved.")


if __name__ == "__main__":
    sync_videos()
