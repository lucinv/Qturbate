from pydantic import BaseModel, HttpUrl, Field
from flask_sqlalchemy import SQLAlchemy

class Video(BaseModel):
    id: str
    title: str = Field(..., example="A Great Video")  # Champs obligatoire avec exemple
    thumbnail_url: HttpUrl  # Validation de format d'URL
    stream_url: HttpUrl
    description: str = None  # Champs optionnel
    tags: list = []

db = SQLAlchemy()

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)

