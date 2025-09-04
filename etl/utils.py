from datetime import datetime
import logging
import config


def dateToStr(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def strToDate(dateStr: str) -> datetime:
    return datetime.strptime(dateStr, "%Y-%m-%d")


def configureLogger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        filename=config.LOG_PATH,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.DEBUG,
        filemode="w",
    )
    return logger


def logCik(loggerFn, cik: str, msg: str):
    loggerFn(f"CIK {cik}: {msg}")