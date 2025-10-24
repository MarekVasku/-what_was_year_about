import os

import gspread
import pandas as pd
import json

# Ensure correct path to credentials.json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

def fetch_data():
    """Authenticate and load Google Sheet data.

    Preference order for credentials:
    1) GOOGLE_SHEETS_CREDENTIALS env var (JSON content of service account)
    2) GOOGLE_APPLICATION_CREDENTIALS env var (path to credentials file)
    3) credentials.json file in project root

    On Hugging Face Spaces, set a repository secret named
    GOOGLE_SHEETS_CREDENTIALS to the full JSON content of your service
    account (paste the JSON starting with {"type": "service_account", ...}).
    """
    gc = None

    # 1) JSON content via env var
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            gc = gspread.service_account_from_dict(creds_dict)
        except Exception:
            gc = None  # Fall through to other methods

    # 2) Path via env var
    if gc is None:
        creds_path_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path_env and os.path.exists(creds_path_env):
            try:
                gc = gspread.service_account(filename=creds_path_env)
            except Exception:
                gc = None

    # 3) Local file
    if gc is None:
        if os.path.exists(CREDENTIALS_PATH):
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
        else:
            raise FileNotFoundError(
                "Google credentials not found. Set the 'GOOGLE_SHEETS_CREDENTIALS' Space secret "
                "with the full JSON content of your service account, or upload 'credentials.json' locally."
            )

    spreadsheet = gc.open("What was 2024 about - responses")
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()

    # Convert to Pandas DataFrame
    df = pd.DataFrame(data)
    return df
