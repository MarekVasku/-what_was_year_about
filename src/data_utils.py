from functools import lru_cache

import numpy as np
import pandas as pd

from load_data import fetch_data

try:
    from sklearn.cluster import KMeans  # type: ignore
    from sklearn.manifold import TSNE  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore
    SKLEARN_AVAILABLE = True
except Exception:
    # Sklearn not available or caused import error, clustering features will be disabled
    SKLEARN_AVAILABLE = False
    KMeans = None  # type: ignore
    StandardScaler = None  # type: ignore
    TSNE = None  # type: ignore


def compute_scores(df: pd.DataFrame | None) -> tuple[pd.DataFrame | None, pd.DataFrame]:
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
        email_prefix: User's email prefix (before @)
        
    Returns:
        tuple[comparison DataFrame, error message or None]
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


def calculate_taste_similarity(df: pd.DataFrame | None, email_prefix: str) -> pd.DataFrame:
    """Calculate correlation between user's votes and all other voters.
    
    Args:
        df: Raw dataframe with votes
        email_prefix: User's email prefix (before @)
        
    Returns:
        DataFrame with voter names and similarity scores (correlation coefficients)
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=['Voter', 'Similarity Score', 'Songs in Common'])

    song_cols = df.columns[2:]
    df_numeric = df[song_cols].apply(pd.to_numeric, errors='coerce')

    # Find user's row
    user_mask = df['Email address'].str.lower().str.split('@').str[0] == email_prefix.lower()
    if not user_mask.any():
        return pd.DataFrame(columns=['Voter', 'Similarity Score', 'Songs in Common'])

    user_votes = df_numeric[user_mask].iloc[0]

    similarities = []
    voter_emails = df['Email address'].tolist()
    for i, (idx, row) in enumerate(df_numeric.iterrows()):
        voter_email = voter_emails[i]
        voter_name = voter_email.split('@')[0]

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
            similarities.append({
                'Voter': voter_name,
                'Similarity Score': correlation,
                'Songs in Common': common_mask.sum()
            })

    if not similarities:
        return pd.DataFrame(columns=['Voter', 'Similarity Score', 'Songs in Common'])

    result = pd.DataFrame(similarities)
    result = result.sort_values('Similarity Score', ascending=False)
    return result


def create_2d_taste_map(df: pd.DataFrame | None, user_email_prefix: str = "") -> pd.DataFrame:
    """Create 2D projection of voters based on their voting patterns.
    
    Args:
        df: Raw dataframe with votes
        user_email_prefix: Current user's email prefix to highlight
        
    Returns:
        DataFrame with X, Y coordinates and voter names
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
        scaler = StandardScaler()  # type: ignore
        df_scaled = scaler.fit_transform(np.array(df_filled))  # type: ignore

        # Use t-SNE for 2D projection (make it more deterministic across envs)
        tsne = TSNE(
            n_components=2,
            random_state=42,
            perplexity=min(5, len(df_filled) - 1),
            init="pca",            # deterministic init
            learning_rate="auto",  # stable default across versions
            max_iter=1000,          # fixed iteration budget (n_iter -> max_iter in newer sklearn)
        )  # type: ignore
        coords_2d = tsne.fit_transform(df_scaled)  # type: ignore

        # Canonicalize location/scale so minor numeric drift doesn't change axes scale wildly
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


def cluster_songs(df: pd.DataFrame | None, n_clusters: int = 5) -> tuple[pd.DataFrame, dict[int, list[str]]]:
    """Cluster songs based on voting patterns.
    
    Args:
        df: Raw dataframe with votes
        n_clusters: Number of clusters to create
        
    Returns:
        Tuple of (DataFrame with song clusters, dict mapping cluster_id to song names)
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=['Song', 'Cluster', 'Cluster_Name']), {}

    song_cols = df.columns[2:]
    df_numeric = df[song_cols].apply(pd.to_numeric, errors='coerce')

    # Transpose so each row is a song, each column is a voter
    song_votes = df_numeric.T

    # Fill NaN with column mean
    song_votes_filled = song_votes.fillna(song_votes.mean())

    # Need at least n_clusters songs
    actual_clusters = min(n_clusters, len(song_votes_filled))
    if actual_clusters < 2:
        return pd.DataFrame(columns=['Song', 'Cluster', 'Cluster_Name']), {}

    if not SKLEARN_AVAILABLE:
        return pd.DataFrame(columns=['Song', 'Cluster', 'Cluster_Name']), {}

    try:
        # Standardize
        scaler = StandardScaler()  # type: ignore
        song_votes_scaled = scaler.fit_transform(np.array(song_votes_filled))  # type: ignore

        # K-means clustering
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)  # type: ignore
        clusters = kmeans.fit_predict(song_votes_scaled)  # type: ignore

        # Create result dataframe
        result = pd.DataFrame({
            'Song': song_cols.tolist(),
            'Cluster': clusters
        })

        # Generate cluster names based on characteristics
        cluster_dict = {}
        cluster_names = {}

        for cluster_id in range(actual_clusters):
            cluster_songs = result[result['Cluster'] == cluster_id]['Song'].tolist()
            cluster_dict[cluster_id] = cluster_songs

            # Calculate cluster characteristics
            cluster_votes = song_votes_filled.iloc[[i for i, s in enumerate(song_cols) if s in cluster_songs]]
            avg_score = cluster_votes.mean().mean()
            std_score = cluster_votes.std().mean()

            # Name based on characteristics
            if avg_score > 7.5:
                name = "⭐ Crowd Favorites"
            elif avg_score < 5:
                name = "😐 Underwhelming Picks"
            elif std_score > 2.5:
                name = "⚡ Polarizing Tracks"
            elif std_score < 1.5:
                name = "🤝 Consensus Picks"
            else:
                name = f"🎵 Group {cluster_id + 1}"

            cluster_names[cluster_id] = name

        result['Cluster_Name'] = result['Cluster'].map(cluster_names)

        return result, cluster_dict
    except Exception as e:
        print(f"Error in song clustering: {e}")
        return pd.DataFrame(columns=['Song', 'Cluster', 'Cluster_Name']), {}


def cluster_voters(df: pd.DataFrame | None, n_clusters: int = 4) -> pd.DataFrame:
    """Cluster voters into taste groups.
    
    Args:
        df: Raw dataframe with votes
        n_clusters: Number of clusters to create
        
    Returns:
        DataFrame with voter names, clusters, and cluster names
    """
    if df is None or df.empty or len(df.columns) < 3:
        return pd.DataFrame(columns=['Voter', 'Cluster', 'Cluster_Name'])

    song_cols = df.columns[2:]
    df_numeric = df[song_cols].apply(pd.to_numeric, errors='coerce')

    # Fill NaN with voter's mean
    df_filled = df_numeric.apply(lambda row: row.fillna(row.mean()), axis=1)

    # Need at least n_clusters voters
    actual_clusters = min(n_clusters, len(df_filled))
    if actual_clusters < 2:
        return pd.DataFrame(columns=['Voter', 'Cluster', 'Cluster_Name'])

    if not SKLEARN_AVAILABLE:
        return pd.DataFrame(columns=['Voter', 'Cluster', 'Cluster_Name'])

    try:
        # Standardize
        scaler = StandardScaler()  # type: ignore
        df_scaled = scaler.fit_transform(np.array(df_filled))  # type: ignore

        # K-means clustering
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)  # type: ignore
        clusters = kmeans.fit_predict(df_scaled)  # type: ignore

        # Create result dataframe
        voter_names = df['Email address'].str.split('@').str[0].tolist()
        result = pd.DataFrame({
            'Voter': voter_names,
            'Cluster': clusters
        })

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

        result['Cluster_Name'] = result['Cluster'].map(cluster_names)

        return result
    except Exception as e:
        print(f"Error in voter clustering: {e}")
        return pd.DataFrame(columns=['Voter', 'Cluster', 'Cluster_Name'])


def refresh_data():
    """Clear cache and reload data.

    We import create_dashboard locally to avoid a circular import at module import time.
    """
    get_data_cached.cache_clear()
    from dashboard import create_dashboard
    return create_dashboard()
