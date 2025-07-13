import requests
import yfinance as yf
from datetime import date
import time
from pprint import pp
import mysql.connector
from dotenv import load_dotenv
import os
import config

load_dotenv()

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

headers = {'User-Agent': config.EMAIL}
response = requests.get(config.URL_SEC_TICKERS, headers=headers)
data = response.json()

# TODO remove when ready for full update
data = list(data.values())[:100]

companies = {
    entry['ticker']: Company(
        str(entry['cik_str']).zfill(10),
        entry['ticker'],
        entry['title']
    ) for entry in data
}

tickers = list(companies.keys())
batch_size = config.BATCH_SIZE_SEC_TICKERS
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

cnx = mysql.connector.connect(host=config.MYSQL_HOST, database=config.MYSQL_DATABASE, user=os.getenv("MYSQL_USER"), password=os.getenv("MYSQL_PASSWORD"))
cursor = cnx.cursor()
for company in companies.values():
    add_company = ("INSERT INTO companies "
                   "(CIK, Ticker, CompanyName, PriceDate, Price) "
                   "VALUES (%s, %s, %s, %s, %s)")
    data_company = (company.cik, company.ticker, company.name, company.priceDate, company.price)
    cursor.execute(add_company, data_company)

cnx.commit()
cursor.close()
cnx.close()