"""Fonctions d'accès aux settings (couche repository)."""
import logging

from storage.models import db, Setting

logger = logging.getLogger(__name__)


def get_setting(key: str) -> str | None:
    setting = Setting.query.filter_by(key=key).first()
    value = setting.value if setting else None
    logger.debug("get_setting(%s) = %s", key, value)
    return value


def set_setting(key: str, value: str) -> None:
    logger.info("set_setting(%s, %s)", key, value)
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()
