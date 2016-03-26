import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_worksheet_data(name):
    with open('credentials.json') as infile:
        data = json.load(infile)

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', ['https://spreadsheets.google.com/feeds'])

    print("Authorizing...")
    gc = gspread.authorize(credentials)

    print('Attempting to open spreadsheet...')
    wks = gc.open(name).sheet1

    print('Fetching all spreadsheet values')
    list_of_lists = wks.get_all_values()

    return list_of_lists
