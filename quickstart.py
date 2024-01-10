import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
# from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

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

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])

    if not values:
      print("No data found.")
      return

    # print("Name, Major:")
    print("Got data from sample sheet:")
    for row in values:
      # Print columns A and E, which correspond to indices 0 and 4.
      print(f"{row[0]}, {row[1]}, {row[2]}")
  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()