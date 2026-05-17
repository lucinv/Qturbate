"""Modèle de domaine Video — pur Pydantic, aucune dépendance externe."""
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class Video(BaseModel):
    id: str
    title: str = Field(..., json_schema_extra={"example": "A Great Video"})
    thumbnail_url: HttpUrl
    stream_url: HttpUrl
    mpv_url: Optional[str] = None
    description: Optional[str] = None
    tags: list = []

    def __init__(self, **data):
        super().__init__(**data)
        self.mpv_url = str(self.stream_url).replace("https://", "mpv://")
