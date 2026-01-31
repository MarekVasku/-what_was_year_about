"""
Custom exception classes for the music survey app.
Provides structured error handling across modules.
"""


class MusicSurveyError(Exception):
    """Base exception for all music survey errors."""
    pass


class CredentialsError(MusicSurveyError):
    """Raised when Google Sheets credentials cannot be loaded or authenticated."""
    pass


class DataError(MusicSurveyError):
    """Raised when data loading or processing fails."""
    pass


class LLMError(MusicSurveyError):
    """Raised when LLM API calls fail or produce invalid responses."""
    pass


class ConfigError(MusicSurveyError):
    """Raised when configuration is missing or invalid."""
    pass


class ValidationError(MusicSurveyError):
    """Raised when data validation fails."""
    pass
