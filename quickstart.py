import os.path
from datetime import date, timedelta
import pprint
import json

import requests
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from polygon import RESTClient
from sec_cik_mapper import StockMapper

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# CIK = 1637207 # PLNT
# CIK = 12659 # HRB
# CIK = 1498710 # SAVE
# CIK = 320193 # AAPL
# CIK = 1543151 # UBER
USER_EMAIL = 'jsripraj@gmail.com'
ASSET_CUTOFF_PERCENTAGE = 0.05


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
    self.financial_data = {}
  
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


class Ticker:
  def __init__(self, code: str, name: str, country: str, exchange: str, currency: str, security_type: str):
    self.code = code
    self.name = name
    self.country = country
    self.exchange = exchange
    self.currency = currency
    self.security_type = security_type


def get_market_cap_google(ticker: str, exchange: str) -> int:
  """
  Returns the market cap of the given ticker trading on the given exchange. 
  This function gets market cap data by scraping Google Finance with BeautifulSoup.
  """
  CUTOFF = 250000000
  url = f"https://www.google.com/finance/quote/{ticker}:{exchange}" 
  try:
    r = requests.get(url)
  except HttpError as error:
    print(f"There was a problem requesting data from Google Finance.")
    raise
  # print(r.text)
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
    if cap < CUTOFF:
      raise Exception(f'Market cap of {cap} below cutoff of {CUTOFF}.')
    return cap
  except AttributeError:
    print(f'Unable to process Google market cap data.')
    raise


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
        filing.financial_data['earnings'] = val
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


# def get_item_value_at_filing(data: dict, item_name: str, filing: Filing) -> (int | None):
#   """
#   Returns the value of the given item_name for the given Filing.
#   Returns None if no value is found.
#   """
#   if not filing:
#     print(f'No filing found.')
#     return None
#   items = data['facts']['us-gaap']
#   # pprint.pprint(items['Assets']['units']['USD'])
#   if 'USD' in items[item_name]['units']:
#     item_filings = items[item_name]['units']['USD']
#     for item_filing in item_filings:
#       if item_filing['accn'] == filing.accn and item_filing['end'] == str(filing.end):
#         res = int(item_filing['val'])
#         # print(res)
#         return res
#   return None


def get_market_cap_yahoo(ticker: str) -> int:
  """
  Returns the market cap of the given ticker. This function gets market cap 
  data by scraping Yahoo Finance with BeautifulSoup.
  """
  url = f"https://finance.yahoo.com/quote/{ticker}"
  try:
    r = requests.get(url)
  except HttpError as error:
    print(f"An error occurred: {error}")
    raise
  # print(r.text)
  soup = BeautifulSoup(r.text, 'html.parser')
  res = soup.find(attrs={"data-test":"MARKET_CAP-value"}) # example res.string = '6.192B'
  try:
    num = float(res.string[:-1])
    multipliers = {
      'T': pow(10, 12),
      'B': pow(10, 9),
      'M': pow(10, 6)
    }
    mult = multipliers[res.string[-1]]
    cap = int(num * mult)
    return cap
  except AttributeError as error:
    print(f'Unable to scrape market cap: {error}')
    raise


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


def test_polygon(ticker):
  with open('polygon_key.txt') as f:
    key = f.read().strip()
  client = RESTClient(api_key=key)
  # url = f'https://api.polygon.io/v1/open-close/{ticker}/{date.today()}?adjusted=true&apiKey={key}'
  # print(f'url = {url}')
  # headers = {'user-agent': USER_EMAIL}
  try:
    for t in client.list_tickers(market="stocks", type="CS", active=True):
      print(t)
    # r = requests.get(url)
    # yesterday = date.today() - timedelta(days=1)
    # r = client.get_previous_close_agg(ticker)
    # pprint.pprint(vars(r[0]))
    # json_data = r.json()
    # pprint.pprint(json_data)
    # return json_data
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


def test_chatgpt(items):
  print('testing chatgpt')
  client = OpenAI()
  
  # test_entries = [
  #   "AccountsPayableCurrent",
  #   "AccountsPayableRelatedPartiesCurrent",
  #   "AccountsPayableRelatedPartiesCurrentAndNoncurrent",
  #   "AccountsPayableRelatedPartiesNoncurrent",
  #   "AccountsReceivableNetCurrent",
  #   "AccountsReceivableRelatedParties",
  #   "AccountsReceivableRelatedPartiesCurrent",
  #   "AccretionAmortizationOfDiscountsAndPremiumsInvestments",
  #   "AccruedLiabilitiesCurrent",
  # ]

  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "user", "content": "I will give you a list of financial statement line items"
        "For each of the items, tell me whether an increase is good, bad, or neutral."
       f"Here is the list: {str(items)}"}
    ]
  )
  resp = completion.choices[0].message.content
  pprint.pprint(resp)
  
  # print(f'len of items is {len(str(items))}')
  # completion = client.chat.completions.create(
  #   model="gpt-3.5-turbo",
  #   messages=[
  #     {"role": "user", "content": "I will give you a list of financial statement line items"
  #      "First, list the items that belong in the Balance Sheet. "
  #      "Second, list the items that belong in the Income Statement. "
  #      "Third, list the items that belong in the Cash Flow Statement. "
  #      f"Here is the list: {str(items)}"}
  #   ]
  # )
  # resp = completion.choices[0].message.content
  # balance_items, income_items, cash_items = resp.split('\n\n')
  # completion = client.chat.completions.create(
  #   model="gpt-3.5-turbo",
  #   messages=[
  #     {"role": "user", 
  #      "content": "I will give you a list of some balance sheet line items."
  #      "Organize them into a typical balance sheet order."
  #      f"Here is the list: {balance_items}"
  #     }
  #   ]
  # )
  # resp = completion.choices[0].message.content
  # print(resp)
  # print(f'resp split into {len(resp)} pieces')
  # for i in range(len(resp)):
  #   print(f'Piece #{i}:\n{resp[i]}\n')


def create_spreadsheet(title, service):
  """
  Creates the Sheet the user has access to.
  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  # pylint: disable=maybe-no-member
  try:
    spreadsheet = {"properties": {"title": title}}
    spreadsheet = (
        service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId")
        .execute()
    )
    # print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get("spreadsheetId")
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error
    

def create_sheets(spreadsheet_id, service):
  requests = []
  requests.append(
    {
      "updateSheetProperties": {
        "properties": {
          "sheetId": 0,
          "title": "Balance Sheet"
        },
        "fields": "title",
      }
    }
  )
  requests.append(
    {
      "addSheet": {
        "properties": {
          "title": "Income Statement"
        }
      }
    }
  )
  requests.append(
    {
      "addSheet": {
        "properties": {
          "title": "Cash Flow Statement"
        }
      }
    }
  )
  
  body = {"requests": requests}
  response = (
    service.spreadsheets()
    .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
    .execute()
  )
  return response


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
  except HttpError:
    print(f"There was a problem requesting data from EDGAR.")
    raise
  except requests.exceptions.JSONDecodeError:
    print(f'Unable to convert EDGAR data to JSON.')
    raise


def edgar_get_company_metadata():
  """
  Returns dictionary of company metadata from EDGAR
  """
  url = f'https://data.sec.gov/submissions/CIK{format_CIK(CIK)}.json'
  headers = {'user-agent': USER_EMAIL}
  try:
    r = requests.get(url, headers=headers)
    json_data = r.json()
    # print(json.dumps(json_data))
    return json_data
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


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


def filter_line_items(data, filings, assets):
  """
  Returns a list of line item names, excluding any items that are not able, in any
  filing, to meet a given percentage of assets.
  """
  output = []
  line_items = data['facts']['us-gaap']
  for name in line_items.keys():
    if "USD" in line_items[name]["units"]:
      for new_filing in line_items[name]["units"]["USD"]:
        # print(f'new_filing = {new_filing}')
        filing = get_filing_by_accn(filings, new_filing['accn'])
        if filing and new_filing['end'] == f'{filing.end}':
          if float(new_filing['val'] >= ASSET_CUTOFF_PERCENTAGE * assets):
            output.append(line_items[name]["label"])
            # print(name)
            # print(f'Label: {line_items[name]["label"]}')
            # print(f'Description: {line_items[name]["description"]}\n')
            break
  return output


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


def format_cik(cik):
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


def update_values(spreadsheet_id, range_name, value_input_option, _values, service):
  """
  Creates the batch_update the user has access to.
  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  # creds, _ = google.auth.default()
  # pylint: disable=maybe-no-member
  try:
    body = {"values": _values}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body,
        )
        .execute()
    )
    print(f"{result.get('updatedCells')} cells updated.")
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


def main():
  """ 
  Run trading robot.
  """
  # Write tickers to file to avoid API calls when testing
  # tickers = get_tickers()
  # with open('tickers.txt', 'w') as f:
  #   json.dump(tickers, f)
  
  with open('tickers.txt', 'r') as f:
    ticker_objs = json.load(f)

  target_year = 2022
  n = len(ticker_objs)
  i = 0
  for code, ticker_obj in ticker_objs.items():
    i += 1
    print(f'({i}/{n}) Ticker: {code}')
    try:
      market_cap = get_market_cap_google(code, ticker_obj['exchange'])
      market_cap = float(market_cap)
      cik = get_cik(code)
      data = edgar_get_data(cik)
      filings = edgar_get_filings(data)
      populate_earnings(data, filings)
      filing = get_filing_by_year(filings, target_year)
      if 'earnings' not in filing.financial_data:
        print(f'No earnings for {target_year} found.')
      earnings22 = float(filing.financial_data['earnings'])
    except Exception as err:
      print(f'Error: {err=}\n')
      continue
    pe = market_cap / earnings22
    print(f'Ticker: {code}, CIK: {cik}, Cap: {round(market_cap)}, Earnings: {round(earnings22)}, PE: {round(pe, 2)}\n')

  """ GOOGLE SHEETS STUFF
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "desktop_credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  """

  # try:
    # service = build("sheets", "v4", credentials=creds)
    # spreadsheet_id = create_spreadsheet("test-report", service)
    # create_sheets(spreadsheet_id, service)
    # company_data = edgar_get_company_metadata()
    # ticker = company_data['tickers'][0]

    # test_polygon(ticker)
    # assets = get_assets(data, filings)
    # line_items = filter_line_items(data, filings, assets)
    # pprint.pprint(line_items)
    # print(f'len of filtered line items = {len(line_items)}')
    # print(*filings, sep="\n")
    # test_chatgpt(line_items)
    # # Pass: spreadsheet_id,  range_name, value_input_option, _values, and service
    # update_values(
    #     spreadsheet_id,
    #     "A1",
    #     "USER_ENTERED",
    #     [data],
    #     service
    # )
  # except HttpError as err:
  #   print(err)


if __name__ == "__main__":
  main()