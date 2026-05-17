"""Tests pour le modèle Video (domaine pur, zéro dépendance externe)."""
from models import Video


def test_video_defaults():
    """Un Video avec le minimum requis doit avoir des valeurs par défaut cohérentes."""
    v = Video(
        id="test_user",
        title="Test Streamer",
        thumbnail_url="https://example.com/thumb.jpg",
        stream_url="https://example.com/stream",
    )
    assert v.id == "test_user"
    assert v.title == "Test Streamer"
    assert v.description is None
    assert v.tags == []
    assert v.mpv_url == "mpv://example.com/stream"


def test_video_with_optional_fields():
    """Les champs optionnels doivent être correctement initialisés."""
    v = Video(
        id="user2",
        title="User 2",
        thumbnail_url="https://example.com/thumb2.jpg",
        stream_url="https://example.com/stream2",
        description="Une super description",
        tags=["asian", "new"],
    )
    assert v.description == "Une super description"
    assert v.tags == ["asian", "new"]


def test_video_mpv_url_construction():
    """mpv_url doit remplacer https:// par mpv://."""
    cases = [
        ("https://chaturbate.com/foo/", "mpv://chaturbate.com/foo/"),
        ("https://example.com/path?a=1", "mpv://example.com/path?a=1"),
    ]
    for stream, expected_mpv in cases:
        v = Video(
            id="test",
            title="Test",
            thumbnail_url="https://example.com/t.jpg",
            stream_url=stream,
        )
        assert v.mpv_url == expected_mpv


def test_video_validation_invalid_url():
    """Une URL invalide doit lever une exception Pydantic."""
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        Video(
            id="test",
            title="Test",
            thumbnail_url="pas-une-url",  # Invalide
            stream_url="https://example.com/s",
        )
