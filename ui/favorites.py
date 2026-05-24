"""Favorites persistence — JSON file store."""

import json
import os
from pathlib import Path

_FAVORITES_DIR = Path(os.path.expanduser("~/.vids"))
_FAVORITES_FILE = _FAVORITES_DIR / "favorites.json"


class FavoritesStore:
    _favorites: set[str] | None = None

    @classmethod
    def _load(cls) -> set[str]:
        if cls._favorites is not None:
            return cls._favorites
        try:
            with open(_FAVORITES_FILE) as f:
                cls._favorites = set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            cls._favorites = set()
        return cls._favorites

    @classmethod
    def _save(cls):
        _FAVORITES_DIR.mkdir(parents=True, exist_ok=True)
        with open(_FAVORITES_FILE, "w") as f:
            json.dump(sorted(cls._favorites), f)

    @classmethod
    def is_favorite(cls, room_id: str) -> bool:
        return room_id in cls._load()

    @classmethod
    def toggle(cls, room_id: str) -> bool:
        favs = cls._load()
        if room_id in favs:
            favs.discard(room_id)
            cls._save()
            return False
        else:
            favs.add(room_id)
            cls._save()
            return True

    @classmethod
    def all(cls) -> list[str]:
        return sorted(cls._load())
