import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

import dashboard

# Add src/ to path so absolute imports work
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))




def _fake_data_tuple():
    # Build a tiny, valid dataset
    df_raw = pd.DataFrame(
        {
            "Timestamp": ["2025-01-01", "2025-01-02"],
            "Email address": ["alice@example.com", "bob@example.com"],
            "Song A": [8, 7],
            "Song B": [9, 0],
            "Song C": [0, 6],
        }
    )
    avg_scores = pd.DataFrame(
        {
            "Song": ["Song A", "Song B", "Song C"],
            "Average Score": [7.5, 9.0, 6.0],
            "Rank": [2, 1, 3],
        }
    )
    total_votes = len(df_raw)
    avg_of_avgs = float(avg_scores["Average Score"].mean())
    total_songs = len(avg_scores)
    error = None
    comparison = None
    return df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, error, comparison


def test_create_dashboard_contract_happy(monkeypatch):
    # Monkeypatch the symbol as used in dashboard.py (dashboard imports it from data_utils)
    monkeypatch.setattr("dashboard.get_data_cached", lambda *args, **kwargs: _fake_data_tuple())

    result = dashboard.create_dashboard("", ranking_view="overlay")

    # Strict length contract
    assert isinstance(result, tuple)
    assert len(result) == 16

    # Type checks on a few key outputs
    overview = result[0]
    podium_chart = result[1]
    top10_chart = result[2]
    main_chart = result[5]
    all_songs_table = result[6]
    comparison_table = result[7]
    taste_map_chart = result[14]
    recommendations_display = result[15]

    assert isinstance(overview, str)
    assert isinstance(podium_chart, go.Figure)
    assert isinstance(top10_chart, go.Figure)
    assert isinstance(main_chart, go.Figure)
    assert isinstance(all_songs_table, pd.DataFrame)
    assert isinstance(comparison_table, pd.DataFrame)
    assert isinstance(taste_map_chart, go.Figure)
    assert isinstance(recommendations_display, str)


def test_create_dashboard_contract_error(monkeypatch):
    # Return an error tuple consistent with get_data_cached's error path
    def _fake_error_tuple(*_args, **_kwargs):
        return None, pd.DataFrame(), 0, 0.0, 0, "Boom", None

    monkeypatch.setattr("dashboard.get_data_cached", _fake_error_tuple)

    result = dashboard.create_dashboard("", ranking_view="overlay")

    assert isinstance(result, tuple)
    assert len(result) == 16

    overview = result[0]
    # Overview should contain an error message string
    assert isinstance(overview, str)
    assert "Error" in overview or "⚠️" in overview

    # Tables should be DataFrames; charts should still be Figures
    assert isinstance(result[6], pd.DataFrame)
    assert isinstance(result[7], pd.DataFrame)
    for i in (1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14):
        assert isinstance(result[i], go.Figure)
