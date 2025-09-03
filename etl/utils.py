from datetime import datetime

def dateToStr(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")
