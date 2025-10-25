import os

import gspread
import pandas as pd
import json

# Ensure correct path to credentials.json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

def _sanitize_headers(headers: list[str]) -> list[str]:
    """Return a list of unique, non-empty headers.

    - Empty/None headers are replaced with col_1, col_2, ... (1-indexed)
    - Duplicate names are suffixed with _2, _3, ... to ensure uniqueness
    """
    cleaned: list[str] = []
    seen: set[str] = set()
    for i, h in enumerate(headers):
        name = (h or "").strip()
        if not name:
            name = f"col_{i+1}"
        base = name
        n = 1
        while name in seen:
            n += 1
            name = f"{base}_{n}"
        seen.add(name)
        cleaned.append(name)
    return cleaned


def _worksheet_to_dataframe(ws: gspread.Worksheet) -> pd.DataFrame:
    """Convert a gspread worksheet to a DataFrame with sanitized headers.

    Uses get_all_values so we can supply our own headers when the first row
    has blanks/duplicates.
    """
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    headers = _sanitize_headers(values[0])
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)
    return df


def fetch_data(year: int = 2024):
    """Authenticate and load Google Sheet data for the specified year.

    Args:
        year: Year to load data for (2019, 2023, or 2024)

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

    # Select spreadsheet and sheet based on year
    if year == 2024:
        spreadsheet = gc.open("What was 2024 about - responses")
        worksheet = spreadsheet.sheet1
        # For 2024 the header row is stable; get_all_records is fine
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    elif year in [2019, 2023]:
        # Older data in one spreadsheet with multiple sheets
        spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1ggWt0Pbpb47qR8XcdUEs7mYxifXh9jY67wEss7hbtsY")
        # Get worksheet by name (assuming sheets are named "2019" and "2023")
        worksheet = spreadsheet.worksheet(str(year))
        # Use a custom header sanitizer to avoid duplicate/blank header errors
        df = _worksheet_to_dataframe(worksheet)
    else:
        raise ValueError(f"Year {year} not supported. Choose from: 2019, 2023, 2024")

    return df
