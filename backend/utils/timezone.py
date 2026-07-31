from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=-6))

def utc_to_cst(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CST)

def get_cst_now() -> datetime:
    return datetime.now(CST)

def get_cst_today():
    return get_cst_now().date()
