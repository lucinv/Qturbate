import asyncio
import cloudscraper
import httpx
from typing import List, Optional
from models import Video
from functools import partial
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://chaturbate.com/api/ts/roomlist/room-list/?limit=90&offset=0"

# Headers simulant une requête AJAX depuis le site
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Referer": "https://chaturbate.com/female-cams/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
}

# Fonction bloquante exécutée dans un thread
def sync_fetch_rooms(gender: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
    scraper = cloudscraper.create_scraper()
    url = BASE_URL
    if gender in ("f", "m", "c"):
        url += f"&genders={gender}"
    if tag:
        url += f"&hashtags={tag}"
    print(f"Fetching rooms with URL: {url}")
    response = scraper.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["rooms"]

# Version async qui appelle la fonction bloquante dans un thread
async def fetch_rooms(gender: Optional[str] = None, tag: Optional[str] = None) -> List[Video]:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        rooms = await loop.run_in_executor(pool, partial(sync_fetch_rooms, gender=gender, tag=tag))

    return [
        Video(
            id=room["username"],
            title=room["username"],
            thumbnail_url=room["img"],
            stream_url=f"https://chaturbate.com/{room['username']}/",
            description=room["subject"],
        )
        for room in rooms
    ]

if __name__ == "__main__":
    videos = asyncio.run(fetch_rooms())
    for video in videos:
        print(video)

