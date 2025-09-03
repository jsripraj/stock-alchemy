import os

EMAIL = "jsripraj@gmail.com"
URL_SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
URL_SEC_COMPANYFACTS = "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
BATCH_SIZE_SEC_TICKERS = 100
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "log")
LOG_PATH = os.path.join(LOG_DIR, "update_financials.log")
ZIP_PATH = os.path.join(DATA_DIR, "companyfacts.zip")
CHUNK_SIZE = 8192