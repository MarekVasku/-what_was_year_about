"""Unit tests for the recommendation function with mocked LLM calls."""
from unittest.mock import patch

import pytest

from llm_implementation import generate_recommendations


class TestGenerateRecommendations:
    """Test suite for generate_recommendations function."""

    def test_successful_recommendations(self):
        """Test successful parsing of valid JSON response."""
        mock_response = '''[
            {"song": "Fred again..", "artist": "", "reason": "Your love for emotional electronic music suggests you'd enjoy Fred's melodic approach."},
            {"song": "Bicep", "artist": "", "reason": "The energetic yet introspective qualities in your top picks align with Bicep's sound."},
            {"song": "Melodic Techno", "artist": "", "reason": "Based on the atmospheric production in your favorites, this genre would resonate."}
        ]'''

        with patch('llm_implementation.call_groq', return_value=mock_response):
            top5 = ["Song A", "Song B", "Song C", "Song D", "Song E"]
            bottom5 = ["Song X", "Song Y", "Song Z", "Song W", "Song V"]

            result = generate_recommendations(top5, bottom5, n=3)

            assert len(result) == 3
            assert result[0]['song'] == "Fred again.."
            assert result[0]['artist'] == ""
            assert "emotional electronic music" in result[0]['reason']

            assert result[1]['song'] == "Bicep"
            assert result[2]['song'] == "Melodic Techno"

    def test_json_wrapped_in_markdown(self):
        """Test extraction of JSON when wrapped in markdown code blocks."""
        mock_response = '''Here are my recommendations:

```json
[
    {"song": "ODESZA", "artist": "", "reason": "Your taste for layered soundscapes matches their production style."}
]
```

Hope this helps!'''

        with patch('llm_implementation.call_groq', return_value=mock_response):
            result = generate_recommendations(["Song A"], ["Song B"], n=1)

            assert len(result) == 1
            assert result[0]['song'] == "ODESZA"

    def test_empty_top5(self):
        """Test that empty top5 returns empty list."""
        result = generate_recommendations([], ["Song X"])
        assert result == []

    def test_malformed_json_returns_fallback(self):
        """Test fallback when JSON parsing fails."""
        mock_response = "This is not valid JSON at all!"

        with patch('llm_implementation.call_groq', return_value=mock_response):
            result = generate_recommendations(["Song A"], ["Song B"])

            assert len(result) == 1
            assert result[0]['song'] == "Unable to analyze taste"
            assert "parse" in result[0]['reason'].lower()

    def test_missing_required_fields(self):
        """Test that recommendations with missing fields are filtered out."""
        mock_response = '''[
            {"song": "Valid Artist", "artist": "", "reason": "Good reason"},
            {"song": "Missing Reason", "artist": ""},
            {"artist": "", "reason": "Missing song field"}
        ]'''

        with patch('llm_implementation.call_groq', return_value=mock_response):
            result = generate_recommendations(["Song A"], ["Song B"], n=5)

            # Only the valid one should be returned
            assert len(result) == 1
            assert result[0]['song'] == "Valid Artist"

    def test_limit_to_n_recommendations(self):
        """Test that results are limited to n even if LLM returns more."""
        mock_response = '''[
            {"song": "Artist 1", "artist": "", "reason": "Reason 1"},
            {"song": "Artist 2", "artist": "", "reason": "Reason 2"},
            {"song": "Artist 3", "artist": "", "reason": "Reason 3"},
            {"song": "Artist 4", "artist": "", "reason": "Reason 4"},
            {"song": "Artist 5", "artist": "", "reason": "Reason 5"},
            {"song": "Artist 6", "artist": "", "reason": "Reason 6"}
        ]'''

        with patch('llm_implementation.call_groq', return_value=mock_response):
            result = generate_recommendations(["Song A"], ["Song B"], n=3)

            assert len(result) == 3
            assert result[0]['song'] == "Artist 1"
            assert result[2]['song'] == "Artist 3"

    def test_exception_handling(self):
        """Test that exceptions are caught and return error message."""
        with patch('llm_implementation.call_groq', side_effect=Exception("API Error")):
            result = generate_recommendations(["Song A"], ["Song B"])

            assert len(result) == 1
            assert "Error generating recommendations" in result[0]['song']
            assert "API Error" in result[0]['reason']

    def test_non_list_response(self):
        """Test handling when LLM returns valid JSON but not a list."""
        mock_response = '{"song": "Not a list", "artist": "", "reason": "This is an object"}'

        with patch('llm_implementation.call_groq', return_value=mock_response):
            result = generate_recommendations(["Song A"], ["Song B"])

            assert len(result) == 1
            assert result[0]['song'] == "Unable to analyze taste"


if __name__ == "__main__":
    # Run with: python -m pytest src/test_recommendations.py -v
    pytest.main([__file__, "-v"])
