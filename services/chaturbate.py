"""Client synchrone pour l'API Chaturbate."""
import logging
from typing import List, Optional

import cloudscraper

from domain.video import Video

logger = logging.getLogger(__name__)

BASE_URL = "https://chaturbate.com/api/ts/roomlist/room-list/?limit=90&offset=0"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Referer": "https://chaturbate.com/female-cams/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
}


def fetch_rooms(gender: Optional[str] = None, tag: Optional[str] = None) -> List[Video]:
    """Récupère la liste des rooms Chaturbate."""
    scraper = cloudscraper.create_scraper()
    url = BASE_URL
    if gender in ("f", "m", "c"):
        url += f"&genders={gender}"
    if tag:
        url += f"&hashtags={tag}"

    logger.info("Fetching rooms from %s", url)
    response = scraper.get(url, headers=HEADERS)
    response.raise_for_status()
    rooms = response.json()["rooms"]
    logger.debug("Got %d rooms", len(rooms))

    return [
        Video(
            id=room["username"],
            title=room["username"],
            thumbnail_url=room["img"],
            stream_url=f"https://chaturbate.com/{room['username']}/",
            description=room.get("subject"),
        )
        for room in rooms
    ]
