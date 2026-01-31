"""
Tests for data utility functions.
Tests score computation, user filtering, and comparisons.
"""

import pandas as pd
import pytest

from data_utils import compute_scores, get_user_votes


class TestComputeScores:
    """Test suite for compute_scores function."""

    def test_compute_scores_basic(self):
        """Test basic score computation with valid data."""
        df = pd.DataFrame(
            {
                "Timestamp": ["2024-01-01", "2024-01-02"],
                "Email": ["user1@test.com", "user2@test.com"],
                "Song A": [8, 9],
                "Song B": [7, 6],
            }
        )

        df_raw, avg_scores = compute_scores(df)

        assert not avg_scores.empty
        assert "Song" in avg_scores.columns
        assert "Average Score" in avg_scores.columns
        assert "Rank" in avg_scores.columns
        assert avg_scores[avg_scores["Song"] == "Song A"]["Average Score"].values[0] == 8.5

    def test_compute_scores_with_ties(self):
        """Test that tied scores get competition ranking."""
        df = pd.DataFrame(
            {
                "Timestamp": ["2024-01-01", "2024-01-02"],
                "Email": ["user1@test.com", "user2@test.com"],
                "Song A": [9.5, 9.5],
                "Song B": [9.5, 9.5],
                "Song C": [8, 8],
            }
        )

        df_raw, avg_scores = compute_scores(df)

        # Both Song A and B should have rank 1 (tied)
        assert (avg_scores["Rank"] == 1).sum() == 2
        # Song C should have rank 3 (competition ranking)
        assert (avg_scores["Rank"] == 3).sum() == 1

    def test_compute_scores_filters_zero_scores(self):
        """Test that songs with zero average score are filtered."""
        df = pd.DataFrame(
            {
                "Timestamp": ["2024-01-01"],
                "Email": ["user1@test.com"],
                "Song A": [5],
                "Song B": [0],
            }
        )

        df_raw, avg_scores = compute_scores(df)

        # Only Song A should remain
        assert len(avg_scores) == 1
        assert avg_scores["Song"].values[0] == "Song A"

    def test_compute_scores_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame()
        df_raw, avg_scores = compute_scores(df)

        assert avg_scores.empty

    def test_compute_scores_coerces_numeric(self):
        """Test that non-numeric values are coerced to NaN."""
        df = pd.DataFrame(
            {
                "Timestamp": ["2024-01-01", "2024-01-02"],
                "Email": ["user1@test.com", "user2@test.com"],
                "Song A": [8, "invalid"],
                "Song B": [7, 6],
            }
        )

        df_raw, avg_scores = compute_scores(df)

        # Should still compute average for Song A (ignoring invalid)
        assert "Song A" in avg_scores["Song"].values


class TestGetUserVotes:
    """Test suite for get_user_votes function."""

    def test_get_user_votes_case_insensitive(self):
        """Test that email matching is case-insensitive."""
        df = pd.DataFrame(
            {
                "Timestamp": ["2024-01-01"],
                "Email address": ["JohnDoe@gmail.com"],
                "Song A": [8],
                "Song B": [7],
            }
        )

        user_votes, error = get_user_votes(df, "johndoe")

        # Should find the user regardless of case
        assert not user_votes.empty
        assert error is None

    def test_get_user_votes_not_found(self):
        """Test handling when user not found."""
        df = pd.DataFrame(
            {
                "Timestamp": ["2024-01-01"],
                "Email address": ["john@gmail.com"],
                "Song A": [8],
                "Song B": [7],
            }
        )

        user_votes, error = get_user_votes(df, "nonexistent")

        assert user_votes.empty
        assert error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
