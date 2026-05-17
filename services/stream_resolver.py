"""Service centralisé d'extraction d'URL de flux via yt-dlp."""
import logging

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def get_direct_stream_url(stream_url: str) -> str | None:
    """Extrait l'URL directe d'un flux à partir de son URL de page."""
    ydl_opts = {
        "format": "best",
        "quiet": True,
    }
    logger.info("Resolving stream URL: %s", stream_url)
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(stream_url, download=False)
        url = info.get("url")
        if url:
            logger.debug("Resolved to: %s", url)
        else:
            logger.warning("No direct URL found for %s", stream_url)
        return url
