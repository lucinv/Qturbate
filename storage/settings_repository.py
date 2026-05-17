"""Fonctions d'accès aux settings (couche repository)."""
from storage.models import db, Setting


def get_setting(key: str) -> str | None:
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else None


def set_setting(key: str, value: str) -> None:
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()
