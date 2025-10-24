import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_main_chart(avg_scores: pd.DataFrame, user_votes: pd.DataFrame | None = None) -> go.Figure:
    """Create main ranking chart with all songs."""
    if avg_scores.empty:
        return go.Figure()

    df_plot = avg_scores.sort_values("Average Score", ascending=True)

    fig = go.Figure()

    # Add average scores
    fig.add_trace(go.Bar(
        x=df_plot["Average Score"],
        y=df_plot["Song"],
        orientation='h',
        name='Average Score',
        marker=dict(
            color=df_plot["Average Score"],
            colorscale='Viridis',
            line=dict(color='rgba(0,0,0,0.2)', width=1),
            showscale=True,
            colorbar=dict(title=dict(text="Score", font=dict(size=12)), thickness=12, len=0.7)
        ),
        hovertemplate='<b>%{y}</b><br>Rank: #%{customdata}<br>Average Score: %{x:.2f}<extra></extra>',
        customdata=df_plot['Rank']
    ))

    # Add user scores if available
    if user_votes is not None and not user_votes.empty:
        user_scores = pd.merge(df_plot[['Song']], user_votes, on='Song', how='left')
        fig.add_trace(go.Bar(
            x=user_scores['Your Score'],
            y=user_scores['Song'],
            orientation='h',
            name='Your Score',
            marker=dict(
                color='rgba(255, 99, 71, 0.7)',
                line=dict(color='rgba(255, 99, 71, 1)', width=1)
            ),
            hovertemplate='<b>%{y}</b><br>Your Score: %{x:.2f}<extra></extra>',
            opacity=0.6
        ))

    fig.update_layout(
        title={
            'text': "Complete Song Ranking",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis_title="Average Score",
        yaxis_title="",
        xaxis=dict(range=[0, 10.5], showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(showgrid=False),
        plot_bgcolor='#fff',
        paper_bgcolor='white',
        barmode='overlay',
        height=max(600, len(df_plot) * 25),
        margin=dict(l=300, r=60, t=80, b=60),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        )
    )

    return fig


def make_main_chart_user_only(comparison: pd.DataFrame | None) -> go.Figure:
    """Create a main ranking chart showing only the user's scores ordered by the user's ranking."""
    if comparison is None or comparison.empty:
        return go.Figure()

    df_plot = comparison.sort_values('Your Score', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot['Your Score'],
        y=df_plot['Song'],
        orientation='h',
        name='Your Score',
        marker=dict(
            color=df_plot['Your Score'],
            colorscale='Viridis',
            line=dict(color='rgba(0,0,0,0.2)', width=1),
            showscale=True,
            colorbar=dict(title=dict(text="Your Score", font=dict(size=12)), thickness=12, len=0.7)
        ),
        hovertemplate='<b>%{y}</b><br>Your Score: %{x:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title={
            'text': "Your Complete Ranking",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis_title="Your Score",
        yaxis_title="",
        xaxis=dict(range=[0, 10.5], showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(showgrid=False),
        plot_bgcolor='#fff',
        paper_bgcolor='white',
        height=max(600, len(df_plot) * 25),
        margin=dict(l=300, r=60, t=80, b=60),
        showlegend=False
    )

    return fig


def make_top_10_spotlight(avg_scores: pd.DataFrame) -> go.Figure:
    """Top-10: no inner bar text; outside-left labels with medal+rank+title+score."""
    if avg_scores.empty:
        return go.Figure()

    top10 = avg_scores.head(10).sort_values("Average Score", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top10["Average Score"],
        y=top10["Song"],
        orientation='h',
        marker=dict(
            color=top10["Average Score"],
            colorscale='Viridis',
            line=dict(color='rgba(0,0,0,0.2)', width=1),
            showscale=False
        ),
        text=None,
        hovertemplate='<b>Rank #%{customdata}</b><br>%{y}<br>Score: %{x:.2f}<extra></extra>',
        customdata=top10['Rank']
    ))

    medal = {1: "🥇", 2: "🥈", 3: "🥉"}
    def label_for_row(row):
        r = int(row["Rank"])
        return f'{medal.get(r, "")} #{r}  {row["Song"]}  •  {row["Average Score"]:.2f}'

    def size_for_rank(r):
        r = int(r)
        return 20 if r == 1 else 18 if r == 2 else 16 if r == 3 else 13

    fig.update_yaxes(showticklabels=False)
    for _, row in top10.iterrows():
        fig.add_annotation(
            x=0, xref="paper",
            y=row["Song"], yref="y",
            text=label_for_row(row),
            showarrow=False,
            xanchor="right",
            xshift=-8,
            align="right",
            font=dict(size=size_for_rank(row["Rank"]), color="#223")
        )

    # Full x-axis from 0 to max with margin
    max_score = float(top10["Average Score"].max())
    x_max = min(10.5, round(max_score + 0.5, 2))

    fig.update_layout(
        title={'text': "Top 10 Songs", 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}},
        plot_bgcolor='#fff', paper_bgcolor='white',
        xaxis=dict(range=[0, x_max], title="Average Score",
                   showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(showgrid=False, title=""),
        height=500,
        margin=dict(l=550, r=100, t=140, b=60),
        bargap=0.30
    )
    return fig


def make_distribution_chart(avg_scores: pd.DataFrame) -> go.Figure:
    """Show score distribution of averages with highlights."""
    if avg_scores.empty:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=avg_scores["Average Score"],
        nbinsx=20,
        marker=dict(
            color='#667eea',
            line=dict(color='rgba(255,255,255,0.3)', width=0.5)
        ),
        hovertemplate='Score Range: %{x}<br>Songs: %{y}<extra></extra>',
        name='Songs'
    ))

    # Add average line
    avg_score = avg_scores["Average Score"].mean()
    fig.add_vline(
        x=avg_score,
        line_dash="dash",
        line_color="#e74c3c",
        line_width=2,
        annotation_text=f"Average: {avg_score:.2f}",
        annotation_position="top right",
        annotation=dict(font=dict(family='Inter', size=11, color='#e74c3c'))
    )

    fig.update_layout(
        title={
            'text': "Average Score Distribution",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#2c3e50'),
        xaxis=dict(
            title="Average Score",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            title="Number of Songs/Votes",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        height=350,
        margin=dict(l=50, r=50, t=0, b=50),
        showlegend=False,
        bargap=0.15
    )

    return fig


def make_all_votes_distribution(df_raw: pd.DataFrame | None) -> go.Figure:
    """Show distribution of ALL individual votes (not averages)."""
    if df_raw is None or df_raw.empty or len(df_raw.columns) < 3:
        return go.Figure()

    song_cols = df_raw.columns[2:]
    all_votes = []

    for col in song_cols:
        votes = pd.to_numeric(df_raw[col], errors='coerce').dropna()
        all_votes.extend(votes.tolist())

    if not all_votes:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=all_votes,
        nbinsx=10,
        marker=dict(
            color='#a78bfa',
            line=dict(color='rgba(255,255,255,0.3)', width=0.5)
        ),
        hovertemplate='Score: %{x}<br>Count: %{y}<extra></extra>',
        name='Individual Votes'
    ))

    # Add average line
    avg_vote = np.mean(all_votes)
    fig.add_vline(
        x=avg_vote,
        line_dash="dash",
        line_color="#e74c3c",
        line_width=2,
        annotation_text=f"Average: {avg_vote:.2f}",
        annotation_position="top right",
        annotation=dict(font=dict(family='Inter', size=11, color='#e74c3c'))
    )

    fig.update_layout(
        title={
            'text': "All Individual Votes Distribution",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        font=dict(family='Inter', color='#2c3e50'),
        xaxis=dict(
            title="Vote Score (1-10)",
            range=[0, 11],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        yaxis=dict(
            title="Number of SongsVotes",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        height=350,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False,
        bargap=0.15
    )

    return fig


def make_podium_chart(avg_scores: pd.DataFrame) -> go.Figure:
    """Podium for ranks 1–3 showing ALL tied songs; smart y-axis zoom with headroom."""
    if avg_scores.empty:
        return go.Figure()

    # Helper: rows for a given rank, sorted nicely
    def rows_for_rank(r: int) -> pd.DataFrame:
        rdf = avg_scores[avg_scores["Rank"] == r].copy()
        if rdf.empty:
            return rdf
        return rdf.sort_values(["Average Score", "Song"], ascending=[False, True])

    # Visual order: 2nd (left), 1st (center), 3rd (right)
    order = [
        (2, "🥈", "#C0C0C0"),
        (1, "🥇", "#FFD700"),
        (3, "🥉", "#CD7F32"),
    ]

    labels, values, colors, hovers, texts = [], [], [], [], []
    for r, medal, color in order:
        r_df = rows_for_rank(r)
        for _, row in r_df.iterrows():
            song = str(row["Song"])
            score = float(row["Average Score"])
            short = song if len(song) <= 32 else (song[:32] + "…")
            labels.append(f"{medal} {short}")
            values.append(score)
            colors.append(color)
            hovers.append(f"<b>{song}</b><br>Score: {score:.2f}")
            texts.append(f"{score:.2f}")

    if not labels:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.5)', width=1)
        ),
        text=texts,
        textposition='outside',
        textfont=dict(size=16, color='#333', family='Inter', weight=500),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hovers,
        showlegend=False,
    ))

    # --- Smart y-axis: zoom into top band, not from zero ---
    y_lo = min(values)
    y_hi = max(values)
    span = max(1e-6, y_hi - y_lo)
    bottom_pad = max(0.5, 0.15 * span)
    top_pad = max(0.6, 0.20 * span)
    y_min = max(0.1, y_lo - bottom_pad)
    y_max = min(10.0, y_hi + top_pad)

    fig.update_layout(
        title={'text': "The Podium", 'x': 0.5, 'xanchor': 'center', 'font': {'size': 26, 'color': '#1a1a1a', 'family': 'Inter'}},
        font=dict(family='Inter', color='#2c3e50'),
        xaxis=dict(
            showgrid=False,
            tickangle=-15,
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            range=[y_min, y_max],
            title="Average Score",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        height=max(440, 340 + 18 * len(labels)),
        margin=dict(l=50, r=50, t=90, b=120),
        bargap=0.35
    )

    return fig


def make_biggest_disagreements_chart(comparison: pd.DataFrame | None) -> go.Figure:
    """Show songs where user differed most from average (top 10 overrated + underrated)."""
    if comparison is None or comparison.empty:
        return go.Figure()

    # Get top 10 most overrated (positive difference) and underrated (negative difference)
    sorted_comp = comparison.sort_values("Difference", ascending=False)
    top_overrated = sorted_comp.head(10)
    top_underrated = sorted_comp.tail(10)

    # Combine and sort by absolute difference
    disagreements = pd.concat([top_overrated, top_underrated]).drop_duplicates()
    disagreements = disagreements.sort_values("Difference", ascending=True)

    # Color coding: red for underrated, green for overrated
    colors = ['#e74c3c' if diff < 0 else '#2ecc71' for diff in disagreements['Difference']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=disagreements['Song'],
        x=disagreements['Difference'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=0.5)
        ),
        text=[f"{d:+.1f}" for d in disagreements['Difference']],
        textposition='outside',
        textfont=dict(family='Inter', size=11),
        hovertemplate='<b>%{y}</b><br>Your Score: %{customdata[0]:.1f}<br>Average: %{customdata[1]:.1f}<br>Difference: %{x:+.1f}<extra></extra>',
        customdata=disagreements[['Your Score', 'Average Score']].values
    ))

    fig.update_layout(
        title={
            'text': "Your Biggest Disagreements with the Group",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        font=dict(family='Inter', color='#2c3e50'),
        xaxis=dict(
            title="Difference from Average (Your Score - Average Score)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        yaxis_title="",
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        height=max(450, len(disagreements) * 25),
        margin=dict(l=320, r=30, t=90, b=60),
        showlegend=False,
    )

    # Add vertical line at 0
    fig.add_vline(x=0, line_dash="dash", line_color="#95a5a6", line_width=1.5, opacity=0.6)

    return fig


def make_user_vs_community_top10(comparison: pd.DataFrame | None, avg_scores: pd.DataFrame) -> go.Figure:
    """Side-by-side comparison of user's top 10 vs community's top 10."""
    if comparison is None or comparison.empty:
        return go.Figure()

    # Get community top 10
    community_top10 = avg_scores.head(10).copy()
    community_top10['Type'] = 'Community'

    # Get user's top 10
    user_top10 = comparison.nlargest(10, 'Your Score').copy()
    user_top10['Type'] = 'Your Top 10'

    # Mark songs that appear in both
    in_both = set(community_top10['Song']) & set(user_top10['Song'])

    fig = go.Figure()

    # Community top 10 (left side, negative x)
    fig.add_trace(go.Bar(
        name='Community Top 10',
        y=community_top10['Song'],
        x=-community_top10['Average Score'],
        orientation='h',
        marker=dict(
            color=['#FFD700' if song in in_both else '#667eea' for song in community_top10['Song']],
            line=dict(color='rgba(255,255,255,0.3)', width=0.5)
        ),
        text=[f"{score:.1f}" for score in community_top10['Average Score']],
        textposition='inside',
        textfont=dict(family='Inter', size=11, color='white'),
        hovertemplate='<b>%{y}</b><br>Average Score: %{customdata:.2f}<extra></extra>',
        customdata=community_top10['Average Score']
    ))

    # User top 10 (right side, positive x)
    fig.add_trace(go.Bar(
        name='Your Top 10',
        y=user_top10['Song'],
        x=user_top10['Your Score'],
        orientation='h',
        marker=dict(
            color=['#FFD700' if song in in_both else '#e74c3c' for song in user_top10['Song']],
            line=dict(color='rgba(255,255,255,0.3)', width=0.5)
        ),
        text=[f"{score:.1f}" for score in user_top10['Your Score']],
        textposition='inside',
        textfont=dict(family='Inter', size=11, color='white'),
        hovertemplate='<b>%{y}</b><br>Your Score: %{x:.2f}<extra></extra>'
    ))

    # Add invisible trace for "In Both" legend entry
    fig.add_trace(go.Bar(
        name='In Both Top 10s',
        x=[0],
        y=[''],
        marker=dict(color='#FFD700'),
        showlegend=True,
        hoverinfo='skip'
    ))

    fig.update_layout(
        title={
            'text': "Your Top 10 vs Community Top 10",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.96,
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'},
            'pad': {'t': 0, 'b': 25}
        },
        font=dict(family='Inter', color='#2c3e50'),
        barmode='overlay',
        xaxis=dict(
            title="← Community Score | Your Score →",
            range=[-11, 11],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='rgba(0,0,0,0.3)'
        ),
        yaxis_title="",
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        height=500,
        margin=dict(l=250, r=100, t=130, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.04,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1,
            font=dict(family='Inter', size=12)
        )
    )

    return fig


def make_voting_heatmap(df_raw: pd.DataFrame | None, email_prefix: str = "") -> go.Figure:
    """Heatmap showing all voters' scores for all songs (anonymized except current user)."""
    if df_raw is None or df_raw.empty or len(df_raw.columns) < 3:
        return go.Figure()

    # Get song columns and voter names
    song_cols = df_raw.columns[2:]
    voters_original = df_raw['Email address'].str.split('@').str[0].tolist()

    # Filter out songs with no votes (all NaN or 0)
    df_numeric = df_raw[song_cols].apply(pd.to_numeric, errors='coerce')
    songs_with_votes = df_numeric.columns[(df_numeric > 0).any()]

    if len(songs_with_votes) == 0:
        return go.Figure()

    # Anonymize voters except current user
    voters = []
    for i, voter in enumerate(voters_original):
        if email_prefix and voter == email_prefix:
            voters.append(voter)  # Keep current user's name
        else:
            voters.append(f"Voter {i+1}")  # Anonymize others

    # Create matrix of scores (only for songs with votes)
    score_matrix = df_numeric[songs_with_votes].values
    song_cols = songs_with_votes

    fig = go.Figure(data=go.Heatmap(
        z=score_matrix,
        x=song_cols,
        y=voters,
        colorscale='RdYlGn',
        zmin=0,
        zmax=10,
        hovertemplate='Voter: %{y}<br>Song: %{x}<br>Score: %{z}<extra></extra>',
        colorbar=dict(title=dict(text="Score", font=dict(size=12)))
    ))

    fig.update_layout(
        title={
            'text': "All Votes Heatmap",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis_title="Songs",
        yaxis_title="Voters",
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=10)),
        height=max(500, len(voters) * 30),
        margin=dict(l=150, r=100, t=80, b=200),
    )

    return fig


def make_controversy_chart(df_raw: pd.DataFrame | None, avg_scores: pd.DataFrame) -> go.Figure:
    """Show standard deviation per song to identify polarizing vs consensus picks."""
    if df_raw is None or df_raw.empty or len(df_raw.columns) < 3:
        return go.Figure()

    song_cols = df_raw.columns[2:]
    df_numeric = df_raw[song_cols].apply(pd.to_numeric, errors='coerce')

    # Calculate standard deviation for each song
    std_devs = df_numeric.std().reset_index()
    std_devs.columns = ['Song', 'Std Dev']

    # Merge with average scores
    controversy = pd.merge(std_devs, avg_scores[['Song', 'Average Score']], on='Song')
    controversy = controversy.sort_values('Std Dev', ascending=False)

    # Top 10 most controversial
    top_controversial = controversy.head(10).sort_values('Std Dev', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_controversial['Song'],
        x=top_controversial['Std Dev'],
        orientation='h',
        marker=dict(
            color=top_controversial['Std Dev'],
            colorscale='OrRd',
            line=dict(color='rgba(255,255,255,0.3)', width=0.5),
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Std Dev",
                    font=dict(family='Inter', size=12)
                ),
                tickfont=dict(family='Inter', size=10),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.1)',
                borderwidth=1
            )
        ),
        text=[f"{std:.2f}" for std in top_controversial['Std Dev']],
        textposition='outside',
        textfont=dict(family='Inter', size=11),
        hovertemplate='<b>%{y}</b><br>Average: %{customdata:.2f}<br>Std Dev: %{x:.2f}<br>(Higher = More Polarizing)<extra></extra>',
        customdata=top_controversial['Average Score']
    ))

    fig.update_layout(
        title={
            'text': "Most Polarizing Songs (Highest Vote Variance)",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        font=dict(family='Inter', color='#2c3e50'),
        xaxis=dict(
            title="Standard Deviation of Scores",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.08)',
            gridwidth=1,
            zeroline=False
        ),
        yaxis_title="",
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        height=max(500, len(top_controversial) * 30),
        margin=dict(l=250, r=100, t=90, b=60),
        showlegend=False,
    )

    return fig


def make_most_agreeable_chart(df_raw: pd.DataFrame | None, avg_scores: pd.DataFrame) -> go.Figure:
    """Show songs with lowest standard deviation (most consensus)."""
    if df_raw is None or df_raw.empty or len(df_raw.columns) < 3:
        return go.Figure()

    song_cols = df_raw.columns[2:]
    df_numeric = df_raw[song_cols].apply(pd.to_numeric, errors='coerce')

    # Calculate standard deviation for each song
    std_devs = df_numeric.std().reset_index()
    std_devs.columns = ['Song', 'Std Dev']

    # Merge with average scores
    agreement = pd.merge(std_devs, avg_scores[['Song', 'Average Score']], on='Song')
    agreement = agreement.sort_values('Std Dev', ascending=True)

    # Top 10 most agreeable (lowest std dev at top)
    top_agreeable = agreement.head(10).sort_values('Std Dev', ascending=False)

    # Invert color values so smallest std dev gets darkest color
    max_std = top_agreeable['Std Dev'].max()
    inverted_colors = max_std - top_agreeable['Std Dev']

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_agreeable['Song'],
        x=top_agreeable['Std Dev'],
        orientation='h',
        marker=dict(
            color=inverted_colors,
            colorscale='Greens',
            line=dict(color='rgba(0,0,0,0.2)', width=1),
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Std Dev",
                    font=dict(family='Inter', size=12)
                ),
                x=1.15,
                tickfont=dict(family='Inter', size=10),
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.1)',
                borderwidth=1,
                tickvals=[0, (max_std - top_agreeable['Std Dev'].min()) / 2, max_std - top_agreeable['Std Dev'].min()],
                ticktext=[f"{top_agreeable['Std Dev'].max():.2f}",
                         f"{(top_agreeable['Std Dev'].max() + top_agreeable['Std Dev'].min()) / 2:.2f}",
                         f"{top_agreeable['Std Dev'].min():.2f}"]
            )
        ),
        text=[f"{std:.2f}" for std in top_agreeable['Std Dev']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Average: %{customdata:.2f}<br>Std Dev: %{x:.2f}<br>(Lower = More Agreement)<extra></extra>',
        customdata=top_agreeable['Average Score']
    ))

    fig.update_layout(
        title={
            'text': "Most Agreeable Songs (Lowest Vote Variance)",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis_title="Standard Deviation of Scores",
        yaxis_title="",
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        height=max(500, len(top_agreeable) * 30),
        margin=dict(l=250, r=100, t=80, b=60),
        showlegend=False,
    )

    return fig


def make_user_rating_pattern(comparison: pd.DataFrame | None, df_raw: pd.DataFrame | None) -> go.Figure:
    """Compare user's score distribution vs community to show if harsh/generous rater."""
    if comparison is None or comparison.empty or df_raw is None or df_raw.empty:
        return go.Figure()

    # Get all community votes
    song_cols = df_raw.columns[2:]
    all_votes = []
    for col in song_cols:
        votes = pd.to_numeric(df_raw[col], errors='coerce').dropna()
        all_votes.extend(votes.tolist())

    # Get user votes
    user_votes = comparison['Your Score'].dropna().tolist()

    if not user_votes or not all_votes:
        return go.Figure()

    fig = go.Figure()

    # Community distribution
    fig.add_trace(go.Histogram(
        x=all_votes,
        name='Community',
        opacity=0.6,
        nbinsx=10,
        marker=dict(color='#4A90E2'),
        histnorm='probability'
    ))

    # User distribution
    fig.add_trace(go.Histogram(
        x=user_votes,
        name='Your Votes',
        opacity=0.6,
        nbinsx=10,
        marker=dict(color='#E74C3C'),
        histnorm='probability'
    ))

    # Calculate stats
    user_avg = np.mean(user_votes)
    community_avg = np.mean(all_votes)
    diff = user_avg - community_avg

    rating_type = "Generous Rater" if diff > 0.5 else "Harsh Critic" if diff < -0.5 else "Balanced Rater"

    fig.update_layout(
        title={
            'text': f"Your Voting Pattern: {rating_type}",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis_title="Score",
        yaxis_title="Proportion of Votes",
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        barmode='overlay',
        height=400,
        margin=dict(l=80, r=80, t=100, b=60),
        annotations=[
            dict(
                text=f"Your Average: {user_avg:.2f} | Community Average: {community_avg:.2f}",
                xref="paper", yref="paper",
                x=0.5, y=1.05,
                showarrow=False,
                font=dict(size=14, color='#666')
            )
        ],
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        )
    )

    return fig


def make_taste_similarity_chart(similarity_df: pd.DataFrame | None) -> go.Figure:
    """Show voters with most similar taste (correlation scores, anonymized)."""
    if similarity_df is None or similarity_df.empty:
        return go.Figure()

    # Show top 10 most similar and anonymize names
    top_similar = similarity_df.head(10).copy()
    top_similar['Voter'] = [f"Similar Voter {i+1}" for i in range(len(top_similar))]
    top_similar = top_similar.sort_values('Similarity Score', ascending=True)

    # Color coding: green for high correlation, yellow for medium
    colors = ['#27AE60' if score > 0.7 else '#F39C12' if score > 0.4 else '#95A5A6'
              for score in top_similar['Similarity Score']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_similar['Voter'],
        x=top_similar['Similarity Score'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0.2)', width=1)),
        text=[f"{score:.2f}" for score in top_similar['Similarity Score']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Similarity: %{x:.2f}<br>Songs in Common: %{customdata}<extra></extra>',
        customdata=top_similar['Songs in Common']
    ))

    fig.update_layout(
        title={
            'text': "Your Taste Twins (Most Similar Voters)",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis_title="Similarity Score (Correlation)",
        xaxis=dict(range=[0, 1]),
        yaxis_title="",
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        height=max(400, len(top_similar) * 40),
        margin=dict(l=150, r=100, t=80, b=60),
        showlegend=False,
    )

    return fig


def make_2d_taste_map_chart(taste_map_df: pd.DataFrame | None) -> go.Figure:
    """Create interactive 2D scatter plot of voter taste positions (anonymized)."""
    if taste_map_df is None or taste_map_df.empty:
        return go.Figure()

    # Separate current user from others and anonymize
    others = taste_map_df[~taste_map_df['Is_Current_User']].copy()
    current_user = taste_map_df[taste_map_df['Is_Current_User']]

    # Anonymize other voters
    others['Voter'] = [f"Voter {i+1}" for i in range(len(others))]

    fig = go.Figure()

    # Add other voters (without text labels)
    if not others.empty:
        fig.add_trace(go.Scatter(
            x=others['X'],
            y=others['Y'],
            mode='markers',
            marker=dict(
                size=10,
                color='#4A90E2',
                line=dict(color='white', width=2)
            ),
            name='Other Voters',
            hovertemplate='<b>%{customdata}</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>',
            customdata=others['Voter']
        ))

    # Add current user (highlighted)
    if not current_user.empty:
        fig.add_trace(go.Scatter(
            x=current_user['X'],
            y=current_user['Y'],
            mode='markers+text',
            marker=dict(
                size=18,
                color='#E74C3C',
                symbol='star',
                line=dict(color='#FFD700', width=3)
            ),
            text=current_user['Voter'],
            textposition='top center',
            textfont=dict(size=12, color='#E74C3C'),
            name='You',
            hovertemplate='<b>%{text} (You)</b><br>X: %{x:.2f}<br>Y: %{y:.2f}<extra></extra>'
        ))

    fig.update_layout(
        title={
            'text': "2D Taste Map",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1a1a1a', 'family': 'Inter'}
        },
        xaxis=dict(
            title="Taste Dimension 1",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=False
        ),
        yaxis=dict(
            title="Taste Dimension 2",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=False
        ),
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=80, r=80, t=80, b=60),
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        )
    )

    return fig


def make_song_clustering_chart(song_clusters_df: pd.DataFrame | None, avg_scores: pd.DataFrame) -> go.Figure:
    """Visualize song clusters with average scores."""
    if song_clusters_df is None or song_clusters_df.empty:
        return go.Figure()

    # Merge with average scores
    merged = pd.merge(song_clusters_df, avg_scores[['Song', 'Average Score']], on='Song', how='left')
    merged = merged.sort_values(['Cluster', 'Average Score'], ascending=[True, False])

    # Create color map for clusters
    unique_clusters = merged['Cluster_Name'].unique()
    color_palette = px.colors.qualitative.Set3
    cluster_colors = {name: color_palette[i % len(color_palette)] for i, name in enumerate(unique_clusters)}

    fig = go.Figure()

    for cluster_name in unique_clusters:
        cluster_data = merged[merged['Cluster_Name'] == cluster_name]

        fig.add_trace(go.Bar(
            y=cluster_data['Song'],
            x=cluster_data['Average Score'],
            orientation='h',
            name=cluster_name,
            marker=dict(
                color=cluster_colors[cluster_name],
                line=dict(color='rgba(0,0,0,0.2)', width=1)
            ),
            text=[f"{score:.1f}" for score in cluster_data['Average Score']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Cluster: ' + cluster_name + '<br>Score: %{x:.2f}<extra></extra>'
        ))

    fig.update_layout(
        title={
            'text': "Song Clusters: Groups with Similar Voting Patterns",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title="Average Score",
        yaxis_title="",
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        height=max(600, len(merged) * 20),
        margin=dict(l=250, r=100, t=80, b=60),
        barmode='group',
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02
        )
    )

    return fig


def make_voter_clustering_chart(voter_clusters_df: pd.DataFrame | None) -> go.Figure:
    """Visualize voter clusters as a bar chart showing distribution."""
    if voter_clusters_df is None or voter_clusters_df.empty:
        return go.Figure()

    # Count voters in each cluster
    cluster_counts = voter_clusters_df.groupby(['Cluster_Name', 'Cluster']).size().reset_index(name='Count')
    cluster_counts = cluster_counts.sort_values('Count', ascending=True)

    # Create color map
    color_palette = px.colors.qualitative.Pastel
    colors = [color_palette[i % len(color_palette)] for i in cluster_counts['Cluster']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=cluster_counts['Cluster_Name'],
        x=cluster_counts['Count'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.2)', width=1)
        ),
        text=cluster_counts['Count'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Voters: %{x}<extra></extra>',
        showlegend=False
    ))

    fig.update_layout(
        title={
            'text': "Voter Archetypes: Taste Groups",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title="Number of Voters",
        yaxis_title="",
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        height=max(400, len(cluster_counts) * 60),
        margin=dict(l=200, r=100, t=80, b=60),
    )

    return fig
