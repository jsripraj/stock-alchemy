from datetime import date
import pprint
import json
import requests

from bs4 import BeautifulSoup
from sec_cik_mapper import StockMapper
from alpaca.trading.client import TradingClient


USER_EMAIL = 'jsripraj@gmail.com'


class Filing:
  """
  Represents a report filed with the SEC.

  Attributes:
    - end: end date of filing period
    - accn: the filing's account number
    - fy: fiscal year
    - fp: fiscal period
    - form: i.e. 10-K, 10-Q, etc.
    - filed: filing date
  """
  def __init__(self, end: date, accn: str, fy: int, fp: str, form: str, filed: date):
    self.end = end 
    self.accn = accn  
    self.fy = fy
    self.fp = fp
    self.form = form
    self.filed = filed
    self.financial_data = Financial_Data()
  
  def __str__(self):
    out = (
      'Filing Object\n'
      f'  end: {self.end}\n'
      f'  accn: {self.accn}\n'
      f'  fy: {self.fy}\n'
      f'  fp: {self.fp}\n'
      f'  form: {self.form}\n'
      f'  filed: {self.filed}\n'
    )
    return out


class Financial_Data():
  def __init__(self, earnings: int=None, earnings_5yr_avg: int=None):
    self.earnings = earnings
    self.earnings_5yr_avg = earnings_5yr_avg


def get_market_cap_google(ticker: str, exchange: str, cutoff: int) -> int:
  """
  Returns the market cap of the given ticker trading on the given exchange. 
  This function gets market cap data by scraping Google Finance with BeautifulSoup.
  """
  url = f"https://www.google.com/finance/quote/{ticker}:{exchange}" 
  try:
    r = requests.get(url)
  except requests.exceptions.RequestException:
    print(f"There was a problem requesting data from Google Finance.")
    raise
  soup = BeautifulSoup(r.text, 'html.parser')
  bs_string = soup.find(string="Market cap")
  if not bs_string:
    raise Exception(f'Google Finance market cap data not found for {ticker} on the {exchange}.')
  try:
    cap_tag = bs_string.parent.parent.next_sibling
    raw_cap_string = cap_tag.string # i.e. "34.23M USD"
    cap_string = raw_cap_string.split(' ')[0]
    num = float(cap_string[:-1])
    multipliers = {
      'T': pow(10, 12),
      'B': pow(10, 9),
      'M': pow(10, 6)
    }
    mult = multipliers[cap_string[-1]]
    cap = int(num * mult)
    if cap < cutoff:
      raise Exception(f'Market cap of {cap} below cutoff of {cutoff}.')
    return cap
  except AttributeError:
    print(f'Unable to process Google market cap data.')
    raise


def populate_5yr_avg_earnings(data: dict, filings: list[Filing]) -> None:
  """
  Must call populate_earnings first.
  Stores the 5-year average of earnings as an integer in the most recent Filing.
  """
  most_recent_year = filings[-1].end.year
  current_year = date.today().year
  if most_recent_year < current_year - 2:
    raise Exception(f'Most recent filing ({most_recent_year}) is too old to compute average earnings.')
  if len(filings) < 5:
    raise Exception(f'{len(filings)} years of filings is not enough to compute average earnings.')
  earnings_sum = 0
  for i in range(-1, -6, -1):
    earnings = filings[i].financial_data.earnings
    if not earnings:
      raise Exception(f'At least one filing in the last five years is missing earnings data.')
    earnings_sum += filings[i].financial_data.earnings
  earnings_avg = earnings_sum / 5
  filings[-1].financial_data.earnings_5yr_avg = round(earnings_avg)
  return


def populate_earnings(data: dict, filings: list[Filing]) -> None:
  """
  Stores the earnings (net income) value as an integer in the corresponding Filing.
  """
  line_items = data['facts']['us-gaap']

  # Get the actual name of the line item
  search_term = 'NetIncomeLoss'
  item_name = None
  for name in line_items.keys():
    # For more complicated searches, may have to use FuzzyWuzzy
    if name.startswith(search_term):
      item_name = name
      break
  if not item_name:
    raise Exception(f'Could not find line item matching {search_term}')

  f = 0 # points to a Filing in filings
  r = 0 # points to a raw_item_filing
  found = False
  try:
    raw_item_filings = line_items[item_name]['units']['USD']
    while f < len(filings) and r < len(raw_item_filings):
      filing = filings[f]
      raw_item_filing = raw_item_filings[r]
      raw_date = edgar_date_string_to_date(raw_item_filing['end'])
      if raw_item_filing['accn'] == filing.accn and raw_date == filing.end:
        val = int(raw_item_filing['val'])
        filing.financial_data.earnings = val
        found = True
        f += 1
      elif raw_date < filing.end:
        r += 1
      else:
        f += 1
    if not found:
      raise Exception(f'No FYE earnings data found.')
  except KeyError:
    print(f'Unexpected raw item filing format.')
    raise
  return 


def get_tickers() -> dict:
  """
  Returns a dict of all common stock tickers trading on the NYSE and the NASDAQ.
  """
  security_type = 'common_stock'
  exchanges = ['NYSE', 'NASDAQ']
  tickers = {}
  for exchange in exchanges:
    url = f'https://eodhd.com/api/exchange-symbol-list/{exchange}?type={security_type}&api_token=65b5850a9df356.73179775&fmt=json'
    data = requests.get(url).json()
    for ticker in data:
      if ticker['Exchange'] in exchanges:
        tickers[ticker['Code']] = {
          'code': ticker['Code'],
          'name': ticker['Name'], 
          'country': ticker['Country'], 
          'exchange': ticker['Exchange'], 
          'currency': ticker['Currency'], 
          'type': ticker['Type']
        }
  return tickers


def get_cik(ticker: str):
  """
  Returns the CIK corresponding to the given ticker
  """
  mapper = StockMapper()
  try:
    cik = mapper.ticker_to_cik[ticker]
  except KeyError as err:
    print(f'Unable to map ticker {ticker} to CIK')
    raise
  return format_cik(cik)


def edgar_get_data(cik: str) -> dict:
  """
  Returns company data obtained from EDGAR.
  """
  url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
  headers = {'user-agent': USER_EMAIL}
  try:
    r = requests.get(url, headers=headers)
    json_data = r.json()
    return json_data
  except requests.exceptions.JSONDecodeError:
    print(f'Unable to convert EDGAR data to JSON.')
    raise
  except requests.exceptions.RequestException:
    print(f"There was a problem requesting data from EDGAR.")
    raise


def edgar_get_company_metadata(cik: int | str) -> dict:
  """
  Returns dictionary of company metadata from EDGAR
  """
  url = f'https://data.sec.gov/submissions/CIK{format_cik(cik)}.json'
  headers = {'user-agent': USER_EMAIL}
  try:
    r = requests.get(url, headers=headers)
    json_data = r.json()
    return json_data
  except requests.exceptions.RequestException as error:
    print(f"There was a problem getting company metadata.")
    raise


def edgar_get_filings(data: dict) -> list[Filing]:
  """
  Returns a chronological list of FYE Filings. 
  """
  try:
    raw_filings = data["facts"]["us-gaap"]["Assets"]["units"]["USD"]
  except KeyError:
    print(f'Could not retrieve raw filings from data. Probably due to an unexpected currency.')
    raise
  output_filings = []
  for raw_filing in raw_filings:
    try:
      if raw_filing['fp'] == 'FY':
        end_date = edgar_date_string_to_date(raw_filing['end'])
        filed_date = edgar_date_string_to_date(raw_filing['filed'])
        # Make sure fiscal year makes sense and time to file is less than half a year 
        if raw_filing['fy'] <= end_date.year and (filed_date - end_date).days < 180:
          output_filings.append(Filing(end_date, raw_filing['accn'], int(raw_filing['fy']), raw_filing['fp'], raw_filing['form'], filed_date))
    except KeyError:
      print(f'Raw filing data has unexpected format.')
      raise
  if not output_filings:
    raise Exception(f'No FYE filings found.')
  return output_filings


def get_assets(data, filings):
  """
  Returns the value of Assets from the most recent fiscal year. 
  Assets will be used to calculate a cutoff to filter out less material financial items.
  """
  if filings[-1].fy == 'FY':
    i = -1
  else:
    i = -2
  asset_filings = data["facts"]["us-gaap"]["Assets"]["units"]["USD"]
  for asset_filing in asset_filings:
    accn = asset_filing['accn']
    end = edgar_date_string_to_date(asset_filing['end'])
    if accn == filings[i].accn and end == filings[i].end:
      return int(asset_filing['val'])


def get_filing_by_accn(filings, accn):
  """
  Returns the Filings object with the given accn.
  If no matching Filing is found, returns None.
  """
  for f in filings:
    if f.accn == accn:
      return f
  return None


def get_filing_by_year(filings: list[Filing], year: int) -> Filing:
  """
  Returns the Filing corresponding to the given year.
  """
  if not filings:
    raise Exception(f'Filing list is empty')
  for f in filings:
    if f.end.year == year:
      return f
  raise Exception(f'No filing for {year} found')


def format_cik(cik: int | str) -> str:
  """
  Returns a 10-digit string representation of a given CIK.
  """
  cik = str(cik)
  out = ('0' * (10 - len(cik))) + cik
  return out
  

def edgar_date_string_to_date(date_str):
  """
  Takes a date string in the form yyyy-mm-dd (such as those obtained from the
  EDGAR API) and returns a Python date object.
  """
  d = [int(x) for x in date_str.split('-')]
  return date(d[0], d[1], d[2])


def play_with_alpaca():
  with open('alpaca_keys.txt', 'r') as f:
    line = f.readline()
    api_key = line.strip().split('=')[1]
    line = f.readline()
    secret_key = line.strip().split('=')[1]
  
  trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=True)
  account = trading_client.get_account()
  pprint.pprint(account)


def main():
  """ 
  Run trading robot.
  """
  target_year = 2022
  MARKET_CAP_CUTOFF = pow(10, 12)

  # Use this in production
  # tickers = get_tickers()

  # But in development, read tickers from file to avoid too many API calls
  with open('tickers.txt', 'r') as f:
    ticker_objs = json.load(f)

  # Use this to write tickers to file
  # with open('tickers.txt', 'w') as f:
  #   json.dump(tickers, f)

  n = len(ticker_objs)
  i = 0
  for code, ticker_obj in ticker_objs.items():
    i += 1
    print(f'({i}/{n}) Ticker: {code}')
    try:
      market_cap = get_market_cap_google(code, ticker_obj['exchange'], MARKET_CAP_CUTOFF)
      market_cap = float(market_cap)
      cik = get_cik(code)
      data = edgar_get_data(cik)
      filings = edgar_get_filings(data)
      populate_earnings(data, filings)
      populate_5yr_avg_earnings(data, filings)
      # filing = get_filing_by_year(filings, target_year)
      filing = filings[-1]
      earnings_5yravg = float(filing.financial_data.earnings_5yr_avg)
    except Exception as err:
      print(f'Error: {err=}\n')
      continue
    pe = market_cap / earnings_5yravg
    print(f'Ticker: {code}, CIK: {cik}, Cap: {round(market_cap)}, 5-Year Average Earnings: {round(earnings_5yravg)}, Price to 5-Year Average Earnings: {round(pe, 2)}\n')


if __name__ == "__main__":
  # main()
  play_with_alpaca()