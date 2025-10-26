"""Core data utilities for loading, computing, and user-specific comparisons.

Contract notes:
- All functions that accept a DataFrame may also accept None/empty; they will return
    empty DataFrames or safe defaults rather than raising, so the UI can render gracefully.
- `get_data_cached` returns a strict tuple used by the UI; its error path returns the same
    shape with `error` set and other values empty/zeroed.
"""

from functools import lru_cache

import numpy as np
import pandas as pd

from load_data import fetch_data

try:
    from sklearn.preprocessing import StandardScaler as SKL_STANDARD_SCALER  # type: ignore
    SKLEARN_AVAILABLE = True
except Exception:
    # Sklearn not available or caused import error; features depending on it will be disabled
    SKLEARN_AVAILABLE = False
    SKL_STANDARD_SCALER = None  # type: ignore


def compute_scores(df: pd.DataFrame | None) -> tuple[pd.DataFrame | None, pd.DataFrame]:
    """Compute per-song average scores with tied ranks.

    Inputs:
        df: Raw Google Sheet DataFrame where the first 2 columns are metadata
            (Timestamp, Email address) and remaining columns are song titles with scores.

    Returns:
        (df_raw, avg_scores) where:
        - df_raw: the numeric-coerced copy of input (or None if input invalid)
        - avg_scores: DataFrame with columns [Song, Average Score, Rank]
          Rank uses competition ranking (ties share the same rank, e.g., 1,1,3,4...)
    """
    if df is None or df.empty or len(df.columns) < 3:
        return df, pd.DataFrame(columns=["Song", "Average Score"])

    song_cols = df.columns[2:]
    df = df.copy()
    df[song_cols] = df[song_cols].apply(pd.to_numeric, errors="coerce")

    avg_scores = (
        df[song_cols].mean()
        .dropna()
        .reset_index()
        .rename(columns={"index": "Song", 0: "Average Score"})
    )
    avg_scores = avg_scores[avg_scores["Average Score"] > 0].copy()

    # --- TIED RANKS (competition rank: 1,1,3,4...) ---
    avg_scores["Rank"] = (
        avg_scores["Average Score"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    # Stable ordering for display: by Rank, then score desc, then Song asc
    avg_scores = avg_scores.sort_values(
        by=["Rank", "Average Score", "Song"],
        ascending=[True, False, True]
    ).reset_index(drop=True)

    return df, avg_scores


def get_user_votes(df: pd.DataFrame | None, email_prefix: str) -> tuple[pd.DataFrame, str | None]:
    """Get votes for a specific user by their email prefix.

    Args:
        df: Raw dataframe with votes
        email_prefix: User's email prefix (before @)

    Returns:
        tuple[user's votes as DataFrame, error message or None]
    """
    if df is None or df.empty:
        return pd.DataFrame(), "No data available"

    # Find row where Email address column matches the prefix
    user_row = df[df['Email address'].str.lower().str.split('@').str[0] == email_prefix.lower()]

    if user_row.empty:
        return pd.DataFrame(), f"No votes found for {email_prefix}"

    # Get just the song scores (columns 2 onwards)
    user_votes = user_row.iloc[:, 2:].T.reset_index()
    user_votes.columns = ["Song", "Your Score"]

    # Drop songs with no vote
    user_votes = user_votes[user_votes["Your Score"].notna()].copy()
    user_votes["Your Score"] = pd.to_numeric(user_votes["Your Score"], errors="coerce")

    return user_votes, None


def compare_user_votes(email_prefix: str) -> tuple[pd.DataFrame, str | None]:
    """Compare a user's votes against the average scores.

    Args:
        email_prefix: user's email prefix (before @)

    Returns:
        (comparison, error):
        - comparison: DataFrame with ['Song','Average Score','Your Score','Difference']
          sorted by absolute Difference descending; empty on error/none
        - error: None on success; user-friendly message otherwise
    """
    try:
        df = fetch_data()
        if df is None:
            return pd.DataFrame(), "No data available"
        df_raw, avg_scores = compute_scores(df)
        if df_raw is None:
            return pd.DataFrame(), "Error computing scores"
        user_votes, error = get_user_votes(df_raw, email_prefix)

        if error:
            return pd.DataFrame(), error

        # Merge user votes with average scores
        comparison = pd.merge(
            avg_scores,
            user_votes,
            on="Song",
            how="right"
        )

        # Add difference column
        comparison["Difference"] = comparison["Your Score"] - comparison["Average Score"]

        # Sort by absolute difference (biggest differences first)
        comparison = comparison.sort_values(
            "Difference",
            key=abs,
            ascending=False
        ).reset_index(drop=True)

        return comparison, None

    except Exception as e:
        return pd.DataFrame(), str(e)


@lru_cache(maxsize=2)  # Cache both general stats and per-user comparisons
def get_data_cached(user_email_prefix: str = "") -> tuple[
    pd.DataFrame | None,  # df_raw
    pd.DataFrame,         # avg_scores
    int,                  # total_votes
    float,                # avg_of_avgs
    int,                  # total_songs
    str | None,           # error
    pd.DataFrame | None,  # comparison
]:
    """Fetch and cache data with metrics for the UI.

    Error handling: On failures or missing user, returns a full tuple with
    df_raw=None, empty avg_scores, numeric zeros, and error set to a short message.
    """
    try:
        df = fetch_data()
        df_raw, avg_scores = compute_scores(df)

        # If user email provided, get comparison
        comparison = None
        if user_email_prefix:
            comparison, error = compare_user_votes(user_email_prefix)
            if error:
                return None, pd.DataFrame(), 0, 0.0, 0, error, None

        total_votes = len(df_raw) if df_raw is not None else 0
        avg_of_avgs = avg_scores["Average Score"].mean() if not avg_scores.empty else 0.0
        total_songs = len(avg_scores)

        return df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, None, comparison
    except Exception as e:
        return None, pd.DataFrame(), 0, 0.0, 0, str(e), None





def create_2d_taste_map(df: pd.DataFrame | None, user_email_prefix: str = "") -> pd.DataFrame:
    """Create a deterministic 2D projection of voters based on voting patterns.

    Args:
        df: raw votes DataFrame (first 2 cols metadata, others numeric scores)
        user_email_prefix: current user's email prefix to highlight

    Returns:
        DataFrame with columns ['Voter', 'X', 'Y', 'Is_Current_User'].
        When input is invalid or sklearn unavailable, returns an empty DataFrame.
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=['Voter', 'X', 'Y', 'Is_Current_User'])

    # Use a stable voter order to ensure deterministic t-SNE across environments
    df_sorted = df.sort_values('Email address').reset_index(drop=True)
    song_cols = df_sorted.columns[2:]
    df_numeric = df_sorted[song_cols].apply(pd.to_numeric, errors='coerce')

    # Fill NaN with each voter's own mean (row-wise), not a single scalar from the first row
    # This avoids environment-dependent differences from row ordering
    df_filled = df_numeric.apply(lambda row: row.fillna(row.mean()), axis=1)

    # Need at least 2 voters and some valid data
    if len(df_filled) < 2 or df_filled.isna().all().all():
        return pd.DataFrame(columns=['Voter', 'X', 'Y', 'Is_Current_User'])

    if not SKLEARN_AVAILABLE:
        return pd.DataFrame(columns=['Voter', 'X', 'Y', 'Is_Current_User'])

    try:
        # Standardize the data
        scaler = SKL_STANDARD_SCALER()  # type: ignore
        df_scaled = scaler.fit_transform(np.array(df_filled))  # type: ignore

        # Use MDS (Multidimensional Scaling) for deterministic 2D projection
        # MDS preserves distances between points and is fully deterministic
        from sklearn.manifold import MDS  # type: ignore
        mds = MDS(n_components=2, random_state=42, dissimilarity='euclidean', normalized_stress='auto', n_init=1)  # type: ignore
        coords_2d = mds.fit_transform(df_scaled)  # type: ignore

        # Canonicalize location/scale so axes are consistent
        coords_2d = (coords_2d - coords_2d.mean(axis=0)) / (coords_2d.std(axis=0) + 1e-9)

        # Create result dataframe
        voter_names = df_sorted['Email address'].str.split('@').str[0].tolist()
        result = pd.DataFrame({
            'Voter': voter_names,
            'X': coords_2d[:, 0],
            'Y': coords_2d[:, 1],
            'Is_Current_User': [name.lower() == user_email_prefix.lower() if user_email_prefix else False
                               for name in voter_names]
        })

        return result
    except Exception as e:
        print(f"Error in 2D taste map: {e}")
        return pd.DataFrame(columns=['Voter', 'X', 'Y', 'Is_Current_User'])









