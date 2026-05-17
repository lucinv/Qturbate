"""Tests pour le service Chaturbate (mocked HTTP)."""
from unittest.mock import patch, MagicMock
from services.chaturbate import fetch_rooms


@patch("services.chaturbate.cloudscraper.create_scraper")
def test_fetch_rooms_returns_video_list(mock_create_scraper):
    """Doit retourner une liste d'objets Video."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "rooms": [
            {
                "username": "streamer1",
                "img": "https://example.com/thumb1.jpg",
                "subject": "Salut les gens",
            },
            {
                "username": "streamer2",
                "img": "https://example.com/thumb2.jpg",
                "subject": None,
            },
        ]
    }
    mock_scraper = MagicMock()
    mock_scraper.get.return_value = mock_response
    mock_create_scraper.return_value = mock_scraper

    from domain.video import Video
    videos = fetch_rooms()

    assert len(videos) == 2
    assert all(isinstance(v, Video) for v in videos)
    assert videos[0].id == "streamer1"
    assert videos[0].title == "streamer1"
    assert videos[0].description == "Salut les gens"
    assert videos[1].description is None


@patch("services.chaturbate.cloudscraper.create_scraper")
def test_fetch_rooms_passes_gender_and_tag(mock_create_scraper):
    """Les paramètres gender et tag doivent être passés dans l'URL."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"rooms": []}
    mock_scraper = MagicMock()
    mock_scraper.get.return_value = mock_response
    mock_create_scraper.return_value = mock_scraper

    fetch_rooms(gender="f", tag="asian")

    call_url = mock_scraper.get.call_args[0][0]
    assert "genders=f" in call_url
    assert "hashtags=asian" in call_url
