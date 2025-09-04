from datetime import datetime
import logging
import config


def dateToStr(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def strToDate(dateStr: str) -> datetime:
    return datetime.strptime(dateStr, "%Y-%m-%d")


def configureLogger(logFile: str, level=logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.propagate = False

    fh = logging.FileHandler(logFile, mode="w")
    fh.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    fh.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
    
    return logger


    # logging.basicConfig(
    #     filename=logFile,
    #     format="%(asctime)s %(levelname)s: %(message)s",
    #     datefmt="%m/%d/%Y %I:%M:%S %p",
    #     level=logging.DEBUG,
    #     filemode="w",
    # )
    # logger.propagate = False
    # return logger


def logCik(loggerFn, cik: str, msg: str):
    loggerFn(f"CIK {cik}: {msg}")