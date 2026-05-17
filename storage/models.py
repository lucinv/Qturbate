"""Modèles SQLAlchemy pour la persistance."""
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)
