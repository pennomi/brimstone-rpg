import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

def get_worksheet_data(name):
    with open('credentials.json') as infile:
        data = json.load(infile)

    credentials = SignedJwtAssertionCredentials(
        data['client_email'], data['private_key'].encode(),
        ['https://spreadsheets.google.com/feeds']
    )

    print("Authorizing...")
    gc = gspread.authorize(credentials)

    print('Attempting to open spreadsheet...')
    wks = gc.open(name).sheet1

    print('Fetching all spreadsheet values')
    list_of_lists = wks.get_all_values()

    return list_of_lists
