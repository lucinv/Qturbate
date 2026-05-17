"""Service centralisé d'extraction d'URL de flux via yt-dlp."""
from yt_dlp import YoutubeDL


def get_direct_stream_url(stream_url: str) -> str | None:
    """Extrait l'URL directe d'un flux à partir de son URL de page.

    Args:
        stream_url: URL de la page du stream (ex: https://chaturbate.com/username/)

    Returns:
        L'URL directe du flux (m3u8, etc.) ou None si impossible.
    """
    ydl_opts = {
        "format": "best",
        "quiet": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(stream_url, download=False)
        return info.get("url")
