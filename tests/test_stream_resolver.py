"""Tests pour le résolveur de flux (yt-dlp mocké)."""
from unittest.mock import patch, MagicMock
from utils.yt import get_direct_stream_url


@patch("utils.yt.YoutubeDL")
def test_get_direct_stream_url_success(mock_ydl_class):
    """Doit retourner l'URL directe extraite par yt-dlp."""
    mock_ydl_instance = MagicMock()
    mock_ydl_instance.__enter__.return_value = mock_ydl_instance
    mock_ydl_class.return_value = mock_ydl_instance

    mock_ydl_instance.extract_info.return_value = {
        "url": "https://direct-stream.example.com/playlist.m3u8",
    }

    result = get_direct_stream_url("https://chaturbate.com/streamer1/")

    assert result == "https://direct-stream.example.com/playlist.m3u8"
    mock_ydl_instance.extract_info.assert_called_once_with(
        "https://chaturbate.com/streamer1/", download=False
    )


@patch("utils.yt.YoutubeDL")
def test_get_direct_stream_url_no_url(mock_ydl_class):
    """Doit retourner None si yt-dlp ne trouve pas d'URL."""
    mock_ydl_instance = MagicMock()
    mock_ydl_instance.__enter__.return_value = mock_ydl_instance
    mock_ydl_class.return_value = mock_ydl_instance

    mock_ydl_instance.extract_info.return_value = {"some": "data"}

    result = get_direct_stream_url("https://example.com/stream/")

    assert result is None
