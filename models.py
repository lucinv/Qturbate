from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from flask_sqlalchemy import SQLAlchemy


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


db = SQLAlchemy()


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)
