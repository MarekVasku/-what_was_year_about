import pandas as pd
from functools import lru_cache
from load_data import fetch_data


def compute_scores(df: pd.DataFrame):
    """Compute average scores for each song."""
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


def get_user_votes(df: pd.DataFrame, email_prefix: str) -> tuple[pd.DataFrame, str]:
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


def compare_user_votes(email_prefix: str) -> tuple[pd.DataFrame, str]:
    """Compare a user's votes against the average scores.
    
    Args:
        email_prefix: User's email prefix (before @)
        
    Returns:
        tuple[comparison DataFrame, error message or None]
    """
    try:
        df = fetch_data()
        df_raw, avg_scores = compute_scores(df)
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
def get_data_cached(user_email_prefix: str = ""):
    """Fetch and cache data with metrics."""
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


def refresh_data():
    """Clear cache and reload data.

    We import create_dashboard locally to avoid a circular import at module import time.
    """
    get_data_cached.cache_clear()
    from dashboard import create_dashboard
    return create_dashboard()
