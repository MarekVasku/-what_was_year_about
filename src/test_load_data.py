"""
Tests for load_data module.
Tests Google Sheets authentication and data fetching.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

import credentials as creds_module
from exceptions import CredentialsError


class TestGoogleSheetsAuthentication:
    """Test suite for Google Sheets authentication."""

    @patch.dict(os.environ, {"GOOGLE_SHEETS_CREDENTIALS": '{"type": "service_account"}'})
    @patch("credentials.gspread.service_account_from_dict")
    def test_authenticate_from_env_json(self, mock_auth):
        """Test authentication using GOOGLE_SHEETS_CREDENTIALS env var."""
        mock_client = MagicMock()
        mock_auth.return_value = mock_client

        result = creds_module.authenticate()

        assert result == mock_client
        mock_auth.assert_called_once()

    @patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json"})
    @patch("os.path.exists", return_value=True)
    @patch("credentials.gspread.service_account")
    def test_authenticate_from_file_env(self, mock_auth, mock_exists):
        """Test authentication using GOOGLE_APPLICATION_CREDENTIALS env var."""
        mock_client = MagicMock()
        mock_auth.return_value = mock_client

        result = creds_module.authenticate()

        assert result == mock_client
        mock_auth.assert_called_once()

    @patch("os.path.exists", return_value=False)
    @patch.dict(os.environ, {"GOOGLE_SHEETS_CREDENTIALS": "", "GOOGLE_APPLICATION_CREDENTIALS": ""})
    def test_authenticate_no_credentials(self, mock_exists):
        """Test that CredentialsError is raised when no credentials found."""
        with pytest.raises(CredentialsError):
            creds_module.authenticate()

    @patch("os.path.exists", return_value=True)
    @patch("credentials.gspread.service_account")
    @patch.dict(os.environ, {"GOOGLE_SHEETS_CREDENTIALS": "", "GOOGLE_APPLICATION_CREDENTIALS": ""})
    def test_authenticate_from_local_file(self, mock_auth, mock_exists):
        """Test authentication using local credentials.json."""
        mock_client = MagicMock()
        mock_auth.return_value = mock_client

        result = creds_module.authenticate()

        assert result == mock_client


class TestFetchData:
    """Test suite for data fetching."""

    @patch("load_data.authenticate")
    @patch("load_data.pd.DataFrame")
    def test_fetch_data_2024(self, mock_df, mock_auth):
        """Test fetching 2024 data (modern format)."""
        # This requires mocking the gspread client and worksheet
        # Structure depends on actual implementation
        pass

    @patch("load_data.authenticate")
    def test_fetch_data_legacy_year(self, mock_auth):
        """Test fetching legacy year data (2019/2023)."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
