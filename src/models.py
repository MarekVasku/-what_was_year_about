"""
Dashboard data structures using dataclasses.
Replaces tuple returns with strongly-typed objects.
"""

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go


@dataclass
class DashboardData:
    """Structured return value for create_dashboard()."""

    # Overview and metadata
    overview: str
    total_votes: int
    total_songs: int
    avg_of_avgs: float
    error_message: str = ""

    # Main charts
    podium_plot: go.Figure = None
    top10_plot: go.Figure = None
    main_plot: go.Figure = None
    distribution_plot: go.Figure = None
    all_votes_plot: go.Figure = None

    # Tables
    all_songs_table: pd.DataFrame = None
    user_comparison_table: pd.DataFrame = None

    # User-specific visualizations
    disagreements_plot: go.Figure = None
    user_vs_top10_plot: go.Figure = None
    rating_pattern_plot: go.Figure = None
    heatmap_plot: go.Figure = None
    controversy_plot: go.Figure = None
    agreeable_plot: go.Figure = None

    # Clustering
    taste_map_plot: go.Figure = None

    # Recommendations
    recommendations_display: str = ""

    @property
    def has_error(self) -> bool:
        """Check if dashboard loading encountered an error."""
        return bool(self.error_message)

    @property
    def has_data(self) -> bool:
        """Check if dashboard has valid data loaded."""
        return not self.has_error and self.total_songs > 0

    def to_tuple(self) -> tuple:
        """
        Convert dataclass to tuple for backward compatibility with Gradio.
        Order matches original create_dashboard() return tuple.
        """
        return (
            self.overview,
            self.podium_plot or go.Figure(),
            self.top10_plot or go.Figure(),
            self.distribution_plot or go.Figure(),
            self.all_votes_plot or go.Figure(),
            self.main_plot or go.Figure(),
            self.all_songs_table if self.all_songs_table is not None else pd.DataFrame(),
            self.user_comparison_table if self.user_comparison_table is not None else pd.DataFrame(),
            self.disagreements_plot or go.Figure(),
            self.user_vs_top10_plot or go.Figure(),
            self.heatmap_plot or go.Figure(),
            self.controversy_plot or go.Figure(),
            self.agreeable_plot or go.Figure(),
            self.rating_pattern_plot or go.Figure(),
            self.taste_map_plot or go.Figure(),
            self.recommendations_display,
        )
