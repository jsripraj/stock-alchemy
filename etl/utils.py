from datetime import datetime


def dateToStr(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def strToDate(dateStr: str) -> datetime:
    return datetime.strptime(dateStr, "%Y-%m-%d")
