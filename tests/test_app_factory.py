"""Tests pour l'application factory Flask."""
from unittest.mock import patch
from app_factory import create_app


def test_create_app_development():
    """L'application créée en mode development doit avoir debug=True."""
    app = create_app("development")
    assert app.debug is True
    assert app.testing is False


def test_create_app_testing():
    """L'application créée en mode test doit avoir testing=True et une DB mémoire."""
    app = create_app("testing")
    assert app.testing is True
    assert app.debug is False
    assert "memory" in app.config["SQLALCHEMY_DATABASE_URI"]


def test_create_app_routes():
    """Les routes principales doivent être enregistrées."""
    app = create_app("testing")
    rules = {r.rule for r in app.url_map.iter_rules() if r.rule != "/static/<path:filename>"}
    assert "/" in rules
    assert "/get-download-url" in rules


@patch("app_factory.routes.fetch_rooms")
def test_index_returns_200(mock_fetch_rooms, client):
    """La page d'accueil doit retourner 200 avec des vidéos mockées."""
    mock_fetch_rooms.return_value = []
    response = client.get("/")
    assert response.status_code == 200
    assert b"Video Gallery" in response.data
