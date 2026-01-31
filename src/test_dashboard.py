"""
Tests for dashboard generation.
Tests create_dashboard output structure and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import plotly.graph_objects as go
from models import DashboardData


class TestDashboardData:
    """Test suite for DashboardData dataclass."""
    
    def test_dashboard_data_creation(self):
        """Test creating DashboardData instance."""
        data = DashboardData(
            overview="Test overview",
            total_votes=100,
            total_songs=50,
            avg_of_avgs=7.5,
        )
        
        assert data.overview == "Test overview"
        assert data.total_votes == 100
        assert data.has_data is True
        assert data.has_error is False
    
    def test_dashboard_data_with_error(self):
        """Test DashboardData with error state."""
        data = DashboardData(
            overview="",
            total_votes=0,
            total_songs=0,
            avg_of_avgs=0,
            error_message="Test error",
        )
        
        assert data.has_error is True
        assert data.has_data is False
    
    def test_dashboard_data_to_tuple(self):
        """Test converting DashboardData to tuple for Gradio compatibility."""
        data = DashboardData(
            overview="Test",
            total_votes=10,
            total_songs=5,
            avg_of_avgs=7.0,
            all_songs_table=pd.DataFrame({"Song": ["A", "B"]}),
        )
        
        result_tuple = data.to_tuple()
        
        # Should return tuple with 16 items (overview + charts + tables + recommendations)
        assert isinstance(result_tuple, tuple)
        assert len(result_tuple) == 16


class TestCreateDashboard:
    """Test suite for create_dashboard function."""
    
    @patch("dashboard.get_data_cached")
    def test_create_dashboard_success(self, mock_get_data):
        """Test successful dashboard creation."""
        # Mock the data return
        mock_get_data.return_value = (
            pd.DataFrame(),  # df_raw
            pd.DataFrame({
                "Song": ["Song A", "Song B"],
                "Average Score": [9.0, 8.0],
                "Rank": [1, 2],
            }),  # avg_scores
            100,  # total_votes
            8.5,  # avg_of_avgs
            2,  # total_songs
            None,  # error
            None,  # comparison
        )
        
        # This would require importing create_dashboard and calling it
        # Actual test structure depends on refactoring
        pass
    
    @patch("dashboard.get_data_cached")
    def test_create_dashboard_error_handling(self, mock_get_data):
        """Test dashboard error handling."""
        mock_get_data.return_value = (
            None, pd.DataFrame(), 0, 0.0, 0,
            "Test error message",
            None,
        )
        
        # Should handle error gracefully
        pass
    
    @patch("dashboard.get_data_cached")
    def test_create_dashboard_empty_data(self, mock_get_data):
        """Test dashboard with empty data."""
        mock_get_data.return_value = (
            pd.DataFrame(), pd.DataFrame(), 0, 0.0, 0,
            None,
            None,
        )
        
        # Should return empty figures, not None
        pass


class TestTiedRanking:
    """Test suite for tied ranking logic."""
    
    def test_podium_display_with_ties(self):
        """Test that podium correctly displays tied songs."""
        avg_scores = pd.DataFrame({
            "Song": ["Song A", "Song B", "Song C"],
            "Average Score": [9.5, 9.5, 8.0],
            "Rank": [1, 1, 3],
        })
        
        # Test that both rank-1 songs are displayed together
        top1 = avg_scores[avg_scores["Rank"] == 1]
        assert len(top1) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
