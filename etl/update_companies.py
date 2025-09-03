import requests
import yfinance as yf
from datetime import date
import time
import config
import supabase_utils
import utils


class Company:
    def __init__(self, cik: str, ticker: str, name: str):
        self.cik: str = cik
        self.ticker: str = ticker
        self.name: str = name
        self.priceDate: date = None
        self.closePrice: float = None

    def __str__(self):
        return (
            f"Company object: cik={self.cik}, ticker={self.ticker}, name={self.name}, "
            + f"priceDate={self.priceDate}, closePrice={self.closePrice}"
        )

    def __repr__(self):
        return self.__str__()


headers = {"User-Agent": config.EMAIL}
response = requests.get(config.URL_SEC_TICKERS, headers=headers)
data = response.json()

# TODO remove when ready for full update
data = list(data.values())[:100]

companies = {
    entry["ticker"]: Company(
        str(entry["cik_str"]).zfill(10), entry["ticker"], entry["title"]
    )
    for entry in data
}

tickers = list(companies.keys())
batch_size = config.BATCH_SIZE_SEC_TICKERS
for i in range(0, len(tickers), batch_size):
    batch = tickers[:batch_size]
    data = yf.download(batch, period="1d")["Close"]
    priceDate = data.index[0].to_pydatetime().date()
    for ticker in tickers:
        if ticker in data.columns:
            closePrice = data[ticker].iloc[0]
            companies[ticker].priceDate = priceDate
            companies[ticker].closePrice = closePrice
    time.sleep(1)

rows = [
    {
        "cik": c.cik,
        "ticker": c.ticker,
        "company": c.name,
        "close_date": utils.dateToStr(c.priceDate),
        "close": c.closePrice,
    }
    for c in companies.values()
]

supabase_utils.insert(table="companies", data=rows)