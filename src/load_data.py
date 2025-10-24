import os

import gspread
import pandas as pd

# Ensure correct path to credentials.json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

def fetch_data():
    # Authenticate and load data
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    spreadsheet = gc.open("What was 2024 about - responses")
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()

    # Convert to Pandas DataFrame
    df = pd.DataFrame(data)
    return df
