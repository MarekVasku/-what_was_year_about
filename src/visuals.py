import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


def make_main_chart(avg_scores: pd.DataFrame, user_votes: pd.DataFrame = None):
    """Main chart: no inner bar text; outside-left labels with medal+rank+title+score."""
    if avg_scores.empty:
        return go.Figure()

    df_plot = avg_scores.sort_values("Average Score", ascending=True).copy()

    fig = go.Figure()
    # Add average scores bar
    fig.add_trace(go.Bar(
        x=df_plot["Average Score"],
        y=df_plot["Song"],
        orientation='h',
        name='Average Score',
        marker=dict(
            color=df_plot["Average Score"],
            colorscale='Viridis',
            line=dict(color='rgba(0,0,0,0.1)', width=1),
            showscale=True,
            colorbar=dict(title="Score", thickness=15, len=0.7)
        ),
        text=None,
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
            text=None,
            hovertemplate='<b>%{y}</b><br>Your Score: %{x:.2f}<extra></extra>',
            opacity=0.6
        ))

    medal = {1: "🥇", 2: "🥈", 3: "🥉"}
    def label_for_row(row):
        r = int(row["Rank"])
        return f'{medal.get(r, "")} #{r}  {row["Song"]}  •  {row["Average Score"]:.2f}'

    def size_for_rank(r):
        r = int(r)
        return 20 if r == 1 else 18 if r == 2 else 16 if r == 3 else 13

    # Put labels OUTSIDE on the left: use paper coords (x=0) and a big left margin.
    fig.update_yaxes(showticklabels=False)
    for _, row in df_plot.iterrows():
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

    fig.update_layout(
        title={'text': "Complete 2024 Alternative Songs Ranking", 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 24, 'color': '#2c3e50', 'family': 'Inter, sans-serif'}},
        plot_bgcolor='#fafafa', paper_bgcolor='white',
        font=dict(size=12, family='Inter, sans-serif'),
        xaxis_title="Average Score", yaxis_title="",
        xaxis=dict(range=[0, 10.5], showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(showgrid=False),
        height=max(600, len(df_plot) * 30),
        margin=dict(l=540, r=120, t=80, b=60),
        bargap=0.15,
        barmode='overlay',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    return fig


def make_top_10_spotlight(avg_scores: pd.DataFrame):
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

    fig.update_layout(
        title={'text': "Top 10 Songs", 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 20, 'color': '#2c3e50'}},
        plot_bgcolor='#fff', paper_bgcolor='white',
        xaxis=dict(range=[0, 10.5], title="Average Score",
                   showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(showgrid=False, title=""),
        height=470,
        margin=dict(l=540, r=100, t=70, b=50),
        bargap=0.30
    )
    return fig


def make_distribution_chart(avg_scores: pd.DataFrame):
    """Show score distribution of averages with highlights."""
    if avg_scores.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=avg_scores["Average Score"],
        nbinsx=20,
        marker=dict(
            color='#4A90E2',
            line=dict(color='white', width=1)
        ),
        hovertemplate='Score Range: %{x}<br>Songs: %{y}<extra></extra>',
        name='Songs'
    ))
    
    # Add average line
    avg_score = avg_scores["Average Score"].mean()
    fig.add_vline(
        x=avg_score,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Average: {avg_score:.2f}",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title={
            'text': "Average Score Distribution",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        xaxis_title="Average Score",
        yaxis_title="Number of Songs",
        height=350,
        margin=dict(l=50, r=50, t=70, b=50),
        showlegend=False,
    )
    
    return fig


def make_all_votes_distribution(df_raw: pd.DataFrame):
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
            color='#9B59B6',
            line=dict(color='white', width=1)
        ),
        hovertemplate='Score: %{x}<br>Count: %{y}<extra></extra>',
        name='Individual Votes'
    ))
    
    # Add average line
    avg_vote = np.mean(all_votes)
    fig.add_vline(
        x=avg_vote,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Average: {avg_vote:.2f}",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title={
            'text': "All Individual Votes Distribution",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        plot_bgcolor='#fafafa',
        paper_bgcolor='white',
        xaxis_title="Vote Score (1-10)",
        yaxis_title="Number of Votes",
        xaxis=dict(range=[0, 11]),
        height=350,
        margin=dict(l=50, r=50, t=70, b=50),
        showlegend=False,
    )
    
    return fig


def make_podium_chart(avg_scores: pd.DataFrame):
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
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0.3)', width=2)),
        text=texts,
        textposition='outside',
        textfont=dict(size=16, color='#333'),
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
        title={'text': "The Podium", 'x': 0.5, 'xanchor': 'center', 'font': {'size': 22, 'color': '#2c3e50'}},
        xaxis=dict(showgrid=False, tickangle=-15),
        yaxis=dict(
            range=[y_min, y_max],
            title="Average Score",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
        ),
        plot_bgcolor='#fff',
        paper_bgcolor='white',
        height=max(440, 340 + 18 * len(labels)),
        margin=dict(l=50, r=50, t=80, b=120),
    )

    return fig
