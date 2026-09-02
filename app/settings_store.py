from sqlmodel import Session, select
from app.models import AppSettings


def get_setting(session: Session, key: str, default=None):
    row = session.exec(select(AppSettings).where(AppSettings.key == key)).first()
    return row.value if row else default


def set_setting(session: Session, key: str, value: str):
    row = session.exec(select(AppSettings).where(AppSettings.key == key)).first()
    if row:
        row.value = value
        session.add(row)
    else:
        session.add(AppSettings(key=key, value=value))
    session.commit()


def all_settings(session: Session) -> dict:
    rows = session.exec(select(AppSettings)).all()
    return {r.key: r.value for r in rows}
