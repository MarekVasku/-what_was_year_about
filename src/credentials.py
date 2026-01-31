"""
Centralized Google Sheets authentication.
Implements 3-tier fallback for credential loading.
"""

import json
import os

import gspread

from config import CREDENTIALS_PATH
from exceptions import CredentialsError


def authenticate() -> gspread.Client:
    """
    Authenticate with Google Sheets using 3-tier fallback.

    Priority order:
    1. GOOGLE_SHEETS_CREDENTIALS env var (JSON string) - for Hugging Face Spaces
    2. GOOGLE_APPLICATION_CREDENTIALS env var (file path) - for environments with file access
    3. credentials.json in project root - for local development

    Returns:
        gspread.Client: Authenticated Google Sheets client

    Raises:
        CredentialsError: If no valid credentials found or authentication fails
    """
    gc = None

    # Attempt 1: JSON content via environment variable
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            gc = gspread.service_account_from_dict(creds_dict)
            return gc
        except json.JSONDecodeError:
            # Invalid JSON format, continue to next method
            pass
        except (gspread.exceptions.GSpreadException, ValueError):
            # Authentication failed with this credential, continue to next method
            pass

    # Attempt 2: File path via environment variable
    creds_path_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path_env and os.path.exists(creds_path_env):
        try:
            gc = gspread.service_account(filename=creds_path_env)
            return gc
        except (gspread.exceptions.GSpreadException, ValueError, FileNotFoundError):
            # Failed to authenticate or read file, continue to next method
            pass

    # Attempt 3: Local credentials.json file
    if os.path.exists(CREDENTIALS_PATH):
        try:
            gc = gspread.service_account(filename=str(CREDENTIALS_PATH))
            return gc
        except (gspread.exceptions.GSpreadException, ValueError, FileNotFoundError) as e:
            raise CredentialsError(
                f"Failed to authenticate with credentials.json: {str(e)}"
            ) from e

    # No credentials found
    raise CredentialsError(
        "Google Sheets credentials not found. "
        "Set 'GOOGLE_SHEETS_CREDENTIALS' environment variable (JSON content) "
        "or place credentials.json in project root."
    )
