import httpx
import asyncio
from typing import List
from models import Video

URL = "https://chaturbate.com/api/ts/roomlist/room-list/?limit=90&offset=0"

# Femme
# https://chaturbate.com/api/ts/roomlist/room-list/?genders=f&limit=90&offset=0
# Couple
# https://chaturbate.com/api/ts/roomlist/room-list/?genders=c&limit=90&offset=0
# Tag 
# https://chaturbate.com/api/ts/roomlist/room-list/?genders=c&hashtags=french&limit=90&offset=0

headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Referer": "https://fr.chaturbate.com/female-cams/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cookie": "sessionid=TON_COOKIE_ICI; cf_clearance=TON_CF_CLEARANCE_ICI; ..."  # ⚠️ Mets ton vrai cookie ici
    }

async def fetch_rooms() -> List[Video]:
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=headers)
        response.raise_for_status()  # Vérifie que la requête s'est bien passéelse:

        data = response.json()
            
        videos = [
                Video(
                    id=room["username"],
                    title=room["username"],
                    thumbnail_url=room["img"],
                    stream_url= f"https://chaturbate.com/{room['username']}/",
                    description=room["subject"]
                    )
                for room in data["rooms"]
                ]

        return videos

if __name__ == "__main__":
    videos = asyncio.run(fetch_rooms())
    for video in videos:
        print(video)
