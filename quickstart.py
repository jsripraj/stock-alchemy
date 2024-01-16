import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
# from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
# import google.auth

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
# SAMPLE_SPREADSHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
SAMPLE_SPREADSHEET_ID = "1jCkn8CCRc1gXVGfW3SaRqHa_yKBJPzCVIfPGhrMoO6k" # my "Scratch" sheet
SAMPLE_RANGE_NAME = "Sheet17!A2:C6"


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
      # creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)
    spreadsheet_id = create("test-report", service)
    data = edgar_get()
    # Pass: spreadsheet_id,  range_name, value_input_option, _values, and service
    update_values(
        spreadsheet_id,
        "A1",
        "USER_ENTERED",
        [["Assets", data]],
        service
    )

  #   # Call the Sheets API
  #   sheet = service.spreadsheets()
  #   result = (
  #       sheet.values()
  #       .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
  #       .execute()
  #   )
  #   values = result.get("values", [])

  #   if not values:
  #     print("No data found.")
  #     return

  #   # print("Name, Major:")
  #   print("Got data from sample sheet:")
  #   for row in values:
  #     # Print columns A and E, which correspond to indices 0 and 4.
  #     print(f"{row[0]}, {row[1]}, {row[2]}")
  except HttpError as err:
    print(err)

def create(title, service):
  """
  Creates the Sheet the user has access to.
  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  # creds, _ = google.auth.default()
  # pylint: disable=maybe-no-member
  try:
    # service = build("sheets", "v4", credentials=creds)
    spreadsheet = {"properties": {"title": title}}
    spreadsheet = (
        service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId")
        .execute()
    )
    print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get("spreadsheetId")
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error
    
def edgar_get():
  """
  Retrieves financial information from EDGAR
  """
  url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001637207.json'
  headers = {'user-agent': 'jsripraj@gmail.com'}
  try:
    r = requests.get(url, headers=headers)
    data = r.json()
    val = data["facts"]["us-gaap"]["Assets"]["units"]["USD"][-1]["val"]
    print(val)
    return val
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

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
    # service = build("sheets", "v4", credentials=creds)
    # values = [
    #     [
    #         # Cell values ...
    #     ],
    #     # Additional rows ...
    # ]
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