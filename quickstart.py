import os.path
import requests
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CIK = 1637207
USER_EMAIL = 'jsripraj@gmail.com'

class Filing:
  def __init__(self, end: date, accn: str, fy: int, fp: str, form: str, filed: date):
    self.end = end 
    self.accn = accn  
    self.fy = fy
    self.fp = fp
    self.form = form
    self.filed = filed
  
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


def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
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

  try:
    service = build("sheets", "v4", credentials=creds)
    # spreadsheet_id = create_spreadsheet("test-report", service)
    # create_sheets(spreadsheet_id, service)
    data = edgar_get_data()
    filings = edgar_get_filings(data)
    print(*filings, sep="\n")
    # test_chatgpt(data)
    # # Pass: spreadsheet_id,  range_name, value_input_option, _values, and service
    # update_values(
    #     spreadsheet_id,
    #     "A1",
    #     "USER_ENTERED",
    #     [data],
    #     service
    # )
  except HttpError as err:
    print(err)


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
  
  print(f'len of items is {len(str(items))}')
  # completion = client.chat.completions.create(
  #   model="gpt-3.5-turbo",
  #   messages=[
  #     {"role": "user", "content": "I will give you a list of financial items. Do not add spaces to the names of the items."
  #      "First, list the items that belong in the Balance Sheet. Order the items how they would appear on a typical Balance Sheet"
  #      "Second, list the items that belong in the Income Statement. "
  #      "Third, list the items that belong in the Cash Flow Statement. "
  #      f"Here is the list: {str(items)}"}
  #   ]
  # )
  # print(completion.choices[0].message.content)


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


def edgar_get_data():
  """
  Returns dictionary of the company data from EDGAR
  """
  url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{format_CIK(CIK)}.json'
  headers = {'user-agent': USER_EMAIL}
  try:
    r = requests.get(url, headers=headers)
    json_data = r.json()
    return json_data
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


def edgar_get_filings(data):
  """
  Get the FYE filings from EDGAR and create Filing objects.
  Returns a chronological list of Filing objects.
  """
  filings = data["facts"]["us-gaap"]["Assets"]["units"]["USD"]
  output = []
  for f in filings:
    if f['fp'] == 'FY':
      end_date = edgar_date_string_to_date(f['end'])
      filed_date = edgar_date_string_to_date(f['filed'])
      # Make sure fiscal year makes sense and time to file is less than half a year 
      if f['fy'] <= end_date.year and (filed_date - end_date).days < 180:
        output.append(Filing(end_date, f['accn'], int(f['fy']), f['fp'], f['form'], filed_date))
  if filings[-1]["fp"] != "FY":
    output.append(Filing(end_date, f['accn'], int(f['fy']), f['fp'], f['form'], filed_date))
  return output


def edgar_get_assets():
  """
  Get the value of Assets from EDGAR. Assets will be used to calculate a cutoff to filter
  out less material financial items.
  """
  url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{format_CIK(CIK)}.json'
  headers = {'user-agent': USER_EMAIL}
  try:
    r = requests.get(url, headers=headers)
    json_data = r.json()
    data = json_data["facts"]["us-gaap"]["Assets"]
    return [k for k in data] 
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error


def format_CIK(cik):
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


if __name__ == "__main__":
  main()