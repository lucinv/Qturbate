from pydantic import BaseModel, HttpUrl, Field
from flask_sqlalchemy import SQLAlchemy

class Video(BaseModel):
    id: str
    title: str = Field(..., example="A Great Video")  # Champs obligatoire avec exemple
    thumbnail_url: HttpUrl  # Validation de format d'URL
    stream_url: HttpUrl
    # mpv_url c'est stream_url mais pour le lecteur mpv : on remplace "https://" par "mpv://"
    mpv_url: str = Field(..., example="mpv://example.com/video")  # Champs obligatoire avec exemple
    description: str = None  # Champs optionnel
    tags: list = []

    # fonction d'initialisation ù on crée l'url mpv_url
    def __init__(self, **data):
        super().__init__(**data)
        self.mpv_url = self.stream_url.replace("https://", "mpv://")

db = SQLAlchemy()

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)

