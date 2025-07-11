import requests
import yfinance as yf
from datetime import date
import time
from pprint import pp

class Company:
    def __init__(self, cik: str, ticker: str, name: str):
        self.cik: str = cik
        self.ticker: str = ticker
        self.name: str = name
        self.priceDate: date = None
        self.price: float = None

    def __str__(self):
        return f'Company object: cik={self.cik}, ticker={self.ticker}, name={self.name}, ' + \
               f'priceDate={self.priceDate}, price={self.price}'
    
    def __repr__(self):
        return self.__str__()

email = 'jsripraj@gmail.com'
url = "https://www.sec.gov/files/company_tickers.json"
headers = {'User-Agent': email}
response = requests.get(url, headers=headers)
data = response.json()
data = list(data.values())[:100] # small sample for now

companies = {
    entry['ticker']: Company(
        str(entry['cik_str']).zfill(10),
        entry['ticker'],
        entry['title']
    ) for entry in data
}

tickers = list(companies.keys())
batch_size = 100
for i in range(0, len(tickers), batch_size):
    batch = tickers[:batch_size]
    data = yf.download(batch, period='1d')['Close']
    priceDate = data.index[0].to_pydatetime().date()
    for ticker in tickers:
        if ticker in data.columns:
            price = data[ticker].iloc[0]
            companies[ticker].priceDate = priceDate
            companies[ticker].price = price
    time.sleep(1)

pp(companies)