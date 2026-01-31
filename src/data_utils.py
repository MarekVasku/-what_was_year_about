import math

import numpy as np
import pandas as pd

from cache import CachedDataLoader
from load_data import fetch_data
from settings import settings

try:
    from sklearn.preprocessing import StandardScaler  # type: ignore

    SKLEARN_AVAILABLE = True
except Exception:
    # Sklearn not available or caused import error; features depending on it will be disabled
    SKLEARN_AVAILABLE = False
    STANDARD_SCALER = None  # type: ignore


# Cache for data loading and processing
DATA_CACHE = CachedDataLoader(
    ttl_seconds=settings.cache_ttl_seconds,
    max_size=settings.cache_max_size,
)


def compute_scores(df: pd.DataFrame | None) -> tuple[pd.DataFrame | None, pd.DataFrame]:
    """Compute per-song average scores with tied ranks (competition ranking).

    This function processes raw voting data and computes:
    - Average score per song across all voters
    - Tied ranks using competition ranking (e.g., 1, 1, 3, 4...)
    - Sorted ordering by rank, then score, then song name

    Args:
        df: Raw Google Sheet DataFrame where:
            - First 2 columns are metadata (Timestamp, Email address)
            - Remaining columns are song titles with numeric scores (1-10)

    Returns:
        Tuple containing:
        - df_raw: Numeric-coerced copy of input DataFrame (or None if input invalid)
        - avg_scores: DataFrame with columns ['Song', 'Average Score', 'Rank']
          where Rank uses competition ranking (ties share same rank)
          Empty DataFrame if input is invalid or has no songs
    """
    if df is None or df.empty or len(df.columns) < 3:
        return df, pd.DataFrame(columns=["Song", "Average Score"])

    song_cols = df.columns[2:]
    df = df.copy()
    df[song_cols] = df[song_cols].apply(pd.to_numeric, errors="coerce")

    avg_scores = df[song_cols].mean().dropna().reset_index().rename(columns={"index": "Song", 0: "Average Score"})
    avg_scores = avg_scores[avg_scores["Average Score"] > 0].copy()

    # --- TIED RANKS (competition rank: 1,1,3,4...) ---
    avg_scores["Rank"] = avg_scores["Average Score"].rank(method="min", ascending=False).astype(int)

    # Stable ordering for display: by Rank, then score desc, then Song asc
    avg_scores = avg_scores.sort_values(
        by=["Rank", "Average Score", "Song"], ascending=[True, False, True]
    ).reset_index(drop=True)

    return df, avg_scores


def _standardize_legacy_votes(df: pd.DataFrame | None, year: int) -> pd.DataFrame:
    """Convert legacy layouts (2019/2023) into 2024-like voter-row matrix.

    Desired output columns:
      - 'Timestamp' (empty string)
      - 'Email address' (synthetic: "<voter>@legacy")
      - then one column per song title. If artist available, title = "<song> - <artist>".
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Normalize headers to strings
    df2 = df.copy()
    df2.columns = [str(c).strip() for c in df2.columns]

    # Helper to find a column by exact lower-case name
    def find_col(name: str) -> str | None:
        for c in df2.columns:
            if c.lower().strip() == name:
                return c
        return None

    song_col = find_col("song")
    artist_col = find_col("artist")
    if song_col is None:
        return pd.DataFrame()

    # Build unified title
    if artist_col is not None:
        titles = (df2[song_col].astype(str).str.strip() + " - " + df2[artist_col].astype(str).str.strip()).str.strip()
    else:
        titles = df2[song_col].astype(str).str.strip()

    # Candidate voter columns (exclude metadata-ish columns)
    exclude = {song_col}
    for meta in [artist_col, find_col("order"), find_col("rank"), find_col("average score")]:
        if meta:
            exclude.add(meta)
    candidates = [c for c in df2.columns if c not in exclude]

    def is_vote_column(series: pd.Series) -> bool:
        vals = pd.to_numeric(series, errors="coerce")
        total = vals.notna().sum()
        if total == 0:
            return False
        in_range = vals.between(1, 10, inclusive="both").sum()
        return in_range >= 1 and in_range >= max(1, int(0.1 * total))

    voter_cols = [c for c in candidates if is_vote_column(df2[c])]
    if not voter_cols:
        return pd.DataFrame()

    # Build standardized voter-row matrix (row per voter)
    songs = list(titles)
    rows: list[dict] = []
    for voter in voter_cols:
        vals = pd.to_numeric(df2[voter], errors="coerce")
        row: dict = {"Timestamp": "", "Email address": f"{voter}@legacy"}
        for title, v in zip(songs, vals, strict=False):
            row[title] = float(v) if pd.notna(v) else math.nan
        rows.append(row)

    std = pd.DataFrame(rows)
    fixed = ["Timestamp", "Email address"]
    song_cols = [c for c in std.columns if c not in fixed]
    return std[fixed + sorted(song_cols)]


def _load_year_df(year: int) -> pd.DataFrame:
    """Return a DataFrame appropriate for computations for the given year.

    - 2024: return raw 2024 sheet as-is.
    - 2019/2023: load legacy sheet and standardize to 2024-like format.
    """
    if year == 2024:
        return fetch_data(2024)
    elif year in (2019, 2023):
        raw = fetch_data(year)
        std = _standardize_legacy_votes(raw, year)
        return std if not std.empty else pd.DataFrame()
    else:
        raise ValueError("Unsupported year")


def get_user_votes(df: pd.DataFrame | None, email_prefix: str) -> tuple[pd.DataFrame, str | None]:
    """Get votes for a specific user by their email prefix.

    Args:
        df: Raw dataframe with votes (must have 'Email address' column)
        email_prefix: User's email prefix (the part before @)

    Returns:
        Tuple containing:
        - DataFrame with user's votes (columns: 'Song', 'Your Score')
        - Error message string, or None if successful
    """
    if df is None or df.empty:
        return pd.DataFrame(), "No voting data available. Please try again later."

    if not email_prefix or not email_prefix.strip():
        return pd.DataFrame(), "Please provide a valid email prefix."

    # Validate email address column exists
    if "Email address" not in df.columns:
        return pd.DataFrame(), "Data format error: Email address column not found."

    # Find row where Email address column matches the prefix (case-insensitive)
    try:
        user_row = df[df["Email address"].str.lower().str.split("@").str[0] == email_prefix.lower().strip()]
    except Exception as e:
        return pd.DataFrame(), f"Error searching for user: {str(e)}"

    if user_row.empty:
        return (
            pd.DataFrame(),
            f"No votes found for '{email_prefix}'. Please check your email prefix (the part before @).",
        )

    # Get just the song scores (columns 2 onwards)
    user_votes = user_row.iloc[:, 2:].T.reset_index()
    user_votes.columns = ["Song", "Your Score"]

    # Drop songs with no vote
    user_votes = user_votes[user_votes["Your Score"].notna()].copy()
    user_votes["Your Score"] = pd.to_numeric(user_votes["Your Score"], errors="coerce")

    return user_votes, None


def compare_user_votes(email_prefix: str, year: int = 2024) -> tuple[pd.DataFrame, str | None]:
    """Compare a user's votes against the average scores for a given year.

    Args:
        email_prefix: User's email prefix (the part before @)
        year: Year to load data for (must be in SUPPORTED_YEARS: 2019, 2023, or 2024)

    Returns:
        Tuple containing:
        - DataFrame with columns ['Song', 'Average Score', 'Your Score', 'Difference']
          sorted by absolute Difference descending; empty on error
        - Error message string, or None if successful
    """
    try:
        df = _load_year_df(year)
        if df is None or df.empty:
            return pd.DataFrame(), f"No voting data available for year {year}."

        df_raw, avg_scores = compute_scores(df)
        if df_raw is None or avg_scores.empty:
            return pd.DataFrame(), "Error computing score statistics."

        user_votes, error = get_user_votes(df_raw, email_prefix)

        if error:
            return pd.DataFrame(), error

        # Merge user votes with average scores
        comparison = pd.merge(avg_scores, user_votes, on="Song", how="right")

        # Add difference column (your score minus average)
        comparison["Difference"] = comparison["Your Score"] - comparison["Average Score"]

        # Sort by absolute difference (biggest differences first)
        comparison = comparison.sort_values("Difference", key=abs, ascending=False).reset_index(drop=True)

        return comparison, None

    except ValueError as e:
        return pd.DataFrame(), f"Invalid year selected: {str(e)}"
    except Exception as e:
        return pd.DataFrame(), f"Unexpected error: {str(e)}"


def _get_data_uncached(user_email_prefix: str = "", year: int = 2024):
    """Fetch data with metrics without caching."""
    try:
        df = _load_year_df(year)
        df_raw, avg_scores = compute_scores(df)

        # If user email provided, try to get comparison (but don't fail if user not found)
        comparison = None
        if user_email_prefix:
            comparison, error = compare_user_votes(user_email_prefix, year)
            if error:
                return None, pd.DataFrame(), 0, 0.0, 0, error, None

        total_votes = len(df_raw) if df_raw is not None else 0
        avg_of_avgs = avg_scores["Average Score"].mean() if not avg_scores.empty else 0.0
        total_songs = len(avg_scores)

        return df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, None, comparison
    except Exception as e:
        # Only critical data loading errors go here
        return None, pd.DataFrame(), 0, 0.0, 0, str(e), None


def get_data_cached(user_email_prefix: str = "", year: int = 2024):
    """Fetch and cache data with metrics.

    Args:
        user_email_prefix: User's email prefix for personalized data
        year: Year to load data for (2019, 2023, or 2024)
    """
    cache_key = (user_email_prefix.lower() if user_email_prefix else "", year)
    return DATA_CACHE.get(cache_key, lambda: _get_data_uncached(user_email_prefix, year))


def calculate_taste_similarity(df: pd.DataFrame | None, email_prefix: str) -> pd.DataFrame:
    """Calculate correlation between user's votes and all other voters.

    Args:
        df: Raw dataframe with votes
        email_prefix: User's email prefix (before @)

    Returns:
        DataFrame with voter names and similarity scores (correlation coefficients)
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=["Voter", "Similarity Score", "Songs in Common"])

    song_cols = df.columns[2:]
    df_numeric = df[song_cols].apply(pd.to_numeric, errors="coerce")

    # Find user's row
    user_mask = df["Email address"].str.lower().str.split("@").str[0] == email_prefix.lower()
    if not user_mask.any():
        return pd.DataFrame(columns=["Voter", "Similarity Score", "Songs in Common"])

    user_votes = df_numeric[user_mask].iloc[0]

    similarities = []
    voter_emails = df["Email address"].tolist()
    for i, (_idx, row) in enumerate(df_numeric.iterrows()):
        voter_email = voter_emails[i]
        voter_name = voter_email.split("@")[0]

        # Skip the user themselves
        if voter_name.lower() == email_prefix.lower():
            continue

        # Find songs both voted on
        common_mask = user_votes.notna() & row.notna()
        if common_mask.sum() < 3:  # Need at least 3 songs in common
            continue

        user_common = user_votes[common_mask]
        voter_common = row[common_mask]

        # Calculate correlation
        correlation = user_common.corr(voter_common)

        if pd.notna(correlation):
            similarities.append(
                {"Voter": voter_name, "Similarity Score": correlation, "Songs in Common": common_mask.sum()}
            )

    if not similarities:
        return pd.DataFrame(columns=["Voter", "Similarity Score", "Songs in Common"])

    result = pd.DataFrame(similarities)
    result = result.sort_values("Similarity Score", ascending=False)
    return result


def create_2d_taste_map(df: pd.DataFrame | None, user_email_prefix: str = "") -> pd.DataFrame:
    """Create 2D projection of voters based on their voting patterns.

    Args:
        df: Raw dataframe with votes
        user_email_prefix: Current user's email prefix to highlight

    Returns:
        DataFrame with columns ['Voter', 'X', 'Y', 'Is_Current_User'].
        When input is invalid or sklearn unavailable, returns an empty DataFrame.
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=["Voter", "X", "Y", "Is_Current_User"])

    # Use a stable voter order to ensure deterministic t-SNE across environments
    df_sorted = df.sort_values("Email address").reset_index(drop=True)
    song_cols = df_sorted.columns[2:]
    df_numeric = df_sorted[song_cols].apply(pd.to_numeric, errors="coerce")

    # Fill NaN with each voter's own mean (row-wise), not a single scalar from the first row
    # This avoids environment-dependent differences from row ordering
    df_filled = df_numeric.apply(lambda row: row.fillna(row.mean()), axis=1)

    # Need at least 2 voters and some valid data
    if len(df_filled) < 2 or df_filled.isna().all().all():
        return pd.DataFrame(columns=["Voter", "X", "Y", "Is_Current_User"])

    if not SKLEARN_AVAILABLE:
        return pd.DataFrame(columns=["Voter", "X", "Y", "Is_Current_User"])

    try:
        # Standardize the data
        scaler = StandardScaler()  # type: ignore
        df_scaled = scaler.fit_transform(np.array(df_filled))  # type: ignore

        # Use MDS (Multidimensional Scaling) for deterministic 2D projection
        # MDS preserves distances between points and is fully deterministic
        from sklearn.manifold import MDS  # type: ignore

        mds = MDS(
            n_components=2,
            random_state=42,
            metric_mds=True,  # Use metric_mds parameter for sklearn compatibility
            normalized_stress="auto",
            n_init=1,
            init="classical_mds",  # Set explicit init to avoid future warning
        )
        coords_2d = mds.fit_transform(df_scaled)  # type: ignore

        # Canonicalize location/scale so axes are consistent
        coords_2d = (coords_2d - coords_2d.mean(axis=0)) / (coords_2d.std(axis=0) + 1e-9)

        # Create result dataframe
        voter_names = df_sorted["Email address"].str.split("@").str[0].tolist()
        result = pd.DataFrame(
            {
                "Voter": voter_names,
                "X": coords_2d[:, 0],
                "Y": coords_2d[:, 1],
                "Is_Current_User": [
                    name.lower() == user_email_prefix.lower() if user_email_prefix else False for name in voter_names
                ],
            }
        )

        return result
    except Exception as e:
        print(f"Error in 2D taste map: {e}")
        return pd.DataFrame(columns=["Voter", "X", "Y", "Is_Current_User"])


def cluster_songs(df: pd.DataFrame | None, n_clusters: int = 5) -> tuple[pd.DataFrame, dict[int, list[str]]]:
    """Cluster songs based on voting patterns.

    Args:
        df: Raw dataframe with votes
        n_clusters: Number of clusters to create

    Returns:
        Tuple of (DataFrame with song clusters, dict mapping cluster_id to song names)
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=["Song", "Cluster", "Cluster_Name"]), {}

    song_cols = df.columns[2:]
    df_numeric = df[song_cols].apply(pd.to_numeric, errors="coerce")

    # Fill NaN with column mean
    song_votes_filled = df_numeric.fillna(df_numeric.mean())

    # Need at least n_clusters songs
    actual_clusters = min(n_clusters, len(song_votes_filled.columns))
    if actual_clusters < 2:
        return pd.DataFrame(columns=["Song", "Cluster", "Cluster_Name"]), {}

    if not SKLEARN_AVAILABLE:
        return pd.DataFrame(columns=["Song", "Cluster", "Cluster_Name"]), {}

    try:
        from sklearn.cluster import KMeans  # type: ignore

        # Standardize
        scaler = StandardScaler()  # type: ignore
        df_scaled = scaler.fit_transform(np.array(song_votes_filled.T))  # type: ignore

        # K-means clustering
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)  # type: ignore
        clusters = kmeans.fit_predict(df_scaled)  # type: ignore

        # Create result dataframe
        result = pd.DataFrame({"Song": song_cols.tolist(), "Cluster": clusters})

        # Generate cluster names based on characteristics
        cluster_dict = {}
        cluster_names = {}

        for cluster_id in range(actual_clusters):
            cluster_songs = result[result["Cluster"] == cluster_id]["Song"].tolist()
            cluster_dict[cluster_id] = cluster_songs

            # Calculate cluster characteristics
            cluster_votes = song_votes_filled.iloc[[i for i, s in enumerate(song_cols) if s in cluster_songs]]
            avg_score = cluster_votes.mean().mean()
            std_score = cluster_votes.std().mean()

            # Name based on characteristics
            if avg_score > 7.5:
                name = "Crowd Favorites"
            elif avg_score < 5:
                name = "Underwhelming Picks"
            elif std_score > 2.5:
                name = "Polarizing Tracks"
            elif std_score < 1.5:
                name = "Consensus Picks"
            else:
                name = f"Group {cluster_id + 1}"

            cluster_names[cluster_id] = name

        result["Cluster_Name"] = result["Cluster"].map(cluster_names)

        return result, cluster_dict
    except Exception as e:
        print(f"Error in song clustering: {e}")
        return pd.DataFrame(columns=["Song", "Cluster", "Cluster_Name"]), {}


def cluster_voters(df: pd.DataFrame | None, n_clusters: int = 4) -> pd.DataFrame:
    """Cluster voters into taste groups.

    Args:
        df: Raw dataframe with votes
        n_clusters: Number of clusters to create

    Returns:
        DataFrame with voter names, clusters, and cluster names
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=["Voter", "Cluster", "Cluster_Name"])

    song_cols = df.columns[2:]
    df_numeric = df[song_cols].apply(pd.to_numeric, errors="coerce")

    # Fill NaN with voter's mean
    df_filled = df_numeric.apply(lambda row: row.fillna(row.mean()), axis=1)

    # Need at least n_clusters voters
    actual_clusters = min(n_clusters, len(df_filled))
    if actual_clusters < 2:
        return pd.DataFrame(columns=["Voter", "Cluster", "Cluster_Name"])

    if not SKLEARN_AVAILABLE:
        return pd.DataFrame(columns=["Voter", "Cluster", "Cluster_Name"])

    try:
        from sklearn.cluster import KMeans  # type: ignore

        # Standardize
        scaler = StandardScaler()  # type: ignore
        df_scaled = scaler.fit_transform(np.array(df_filled))  # type: ignore

        # K-means clustering
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)  # type: ignore
        clusters = kmeans.fit_predict(df_scaled)  # type: ignore

        # Create result dataframe
        voter_names = df["Email address"].str.split("@").str[0].tolist()
        result = pd.DataFrame({"Voter": voter_names, "Cluster": clusters})

        # Generate cluster names based on voting patterns
        cluster_names = {}
        for cluster_id in range(actual_clusters):
            cluster_mask = clusters == cluster_id
            cluster_voters = df_filled[cluster_mask]

            if len(cluster_voters) > 0:
                avg_score = float(np.mean(cluster_voters.to_numpy()))
                score_range = float(np.max(cluster_voters.to_numpy()) - np.min(cluster_voters.to_numpy()))
            else:
                avg_score = 0.0
                score_range = 0.0

            # Name based on characteristics
            if avg_score > 8:
                name = "🌟 The Enthusiasts"
            elif avg_score < 5:
                name = "🎭 The Critics"
            elif score_range > 8:
                name = "🎲 The Diverse Tastes"
            elif score_range < 4:
                name = "😌 The Moderates"
            else:
                name = f"👥 Group {cluster_id + 1}"

            cluster_names[cluster_id] = name

        result["Cluster_Name"] = result["Cluster"].map(cluster_names)

        return result
    except Exception as e:
        print(f"Error in voter clustering: {e}")
        return pd.DataFrame(columns=["Voter", "Cluster", "Cluster_Name"])


def refresh_data():
    """Clear cache and reload data.

    We import create_dashboard locally to avoid a circular import at module import time.
    """
    DATA_CACHE.clear()
    from dashboard import create_dashboard

    return create_dashboard()
