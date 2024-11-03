from models import db, Setting

def get_setting(key):
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else None

def set_setting(key, value):
    setting = Setting.query.filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.session.add(setting)
    db.session.commit()

