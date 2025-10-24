# panel_app.py
from functools import lru_cache

import pandas as pd
import panel as pn
import plotly.express as px

from load_data import fetch_data

pn.extension("plotly")

# ---------- data prep ----------
def compute_scores(df: pd.DataFrame):
    """Return (raw_df, avg_scores) where avg_scores has columns [Song, Average Score]."""
    if df is None or df.empty or len(df.columns) < 3:
        return df, pd.DataFrame(columns=["Song", "Average Score"])

    song_cols = df.columns[2:]
    df = df.copy()
    df[song_cols] = df[song_cols].apply(pd.to_numeric, errors="coerce")

    avg_scores = (
        df[song_cols]
        .mean()
        .dropna()
        .reset_index()
        .rename(columns={"index": "Song", 0: "Average Score"})
    )
    # remove zeros and sort ascending so bars grow upward
    avg_scores = avg_scores[avg_scores["Average Score"] > 0].copy()
    avg_scores = avg_scores.sort_values("Average Score", ascending=True).reset_index(drop=True)
    return df, avg_scores

@lru_cache(maxsize=1)
def get_data_cached():
    df = fetch_data()
    raw, avg = compute_scores(df)
    total_votes = len(raw) if raw is not None else 0
    if not avg.empty:
        highest = f"{avg.iloc[-1]['Song']} ({avg.iloc[-1]['Average Score']:.2f})"
        avg_of_avgs = float(avg["Average Score"].mean())
    else:
        highest = "N/A"
        avg_of_avgs = float("nan")
    return raw, avg, total_votes, highest, avg_of_avgs

def refresh_data(event=None):
    get_data_cached.cache_clear()
    render()  # re-draw with fresh data

# ---------- plotting ----------
def make_bar(df_plot: pd.DataFrame):
    fig = px.bar(
        df_plot,
        x="Average Score",
        y="Song",
        orientation="h",
        title="Top Rated Songs",
        text="Average Score",
        color="Average Score",
        color_continuous_scale="darkmint",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis_title="Average Score",
        yaxis_title="Songs",
        title_x=0.5,
        width=1100,
        height=600,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig

def make_hist(avg_scores: pd.DataFrame):
    fig = px.histogram(
        avg_scores,
        x="Average Score",
        nbins=10,
        title="Distribution of Ratings",
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_x=0.5,
        width=1100,
        height=380,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig

# ---------- widgets ----------
min_rating = pn.widgets.FloatSlider(name="Minimum Rating", start=0.0, end=10.0, step=0.1, value=0.0)
topn       = pn.widgets.IntSlider(name="Top N", start=1, end=200, step=1, value=20)
search     = pn.widgets.TextInput(name="Search song", placeholder="type to filter…")
refresh    = pn.widgets.Button(name="🔄 Refresh from Google Sheet", button_type="primary")

# ---------- panes / outputs ----------
metrics_md = pn.pane.Markdown("### 📊 Key Metrics\n_Loading…_")
table_w    = pn.widgets.DataFrame(disabled=True, sizing_mode="stretch_width", height=360)
bar_pane   = pn.pane.Plotly(sizing_mode="stretch_width")
hist_pane  = pn.pane.Plotly(sizing_mode="stretch_width")

def render(event=None):
    """Read cached data, set widget bounds, recompute filters, and update panes."""
    raw, avg, total_votes, highest_txt, avg_all = get_data_cached()

    # set sensible widget bounds based on data
    if not avg.empty:
        min_rating.start = float(avg["Average Score"].min())
        min_rating.end   = float(min(10.0, avg["Average Score"].max()))
        topn.end         = int(len(avg))
        if min_rating.value < min_rating.start:
            min_rating.value = min_rating.start
        if topn.value > topn.end:
            topn.value = min(20, topn.end)
    else:
        min_rating.start = 0.0
        min_rating.end   = 10.0
        min_rating.value = 0.0
        topn.end         = 1
        topn.value       = 1

    # filter
    q = avg.copy()
    if not q.empty:
        if min_rating.value is not None:
            q = q[q["Average Score"] >= float(min_rating.value)]
        if search.value:
            s = search.value.lower()
            q = q[q["Song"].str.lower().str.contains(s, na=False)]
        if topn.value is not None and topn.value > 0:
            q = q.sort_values("Average Score", ascending=False).head(int(topn.value))
            q = q.sort_values("Average Score", ascending=True)
        q = q.reset_index(drop=True)

    # update metrics
    if avg.empty:
        metrics_md.object = "### 📊 Key Metrics\n_No data yet._"
        table_w.value = avg.head(0)
        bar_pane.object = make_bar(avg.head(0))
        hist_pane.object = make_hist(avg.head(0))
        return

    metrics_md.object = f"""### 📊 Key Metrics
- **Total Votes**: {total_votes}
- **Highest Rated**: {highest_txt}
- **Average of Averages**: {avg_all:.2f}
"""

    table_w.value = q[["Song", "Average Score"]]
    bar_pane.object = make_bar(q if not q.empty else avg.head(0))
    hist_pane.object = make_hist(avg)

# react to user input
for w in (min_rating, topn, search):
    w.param.watch(render, "value", onlychanged=True)
refresh.on_click(refresh_data)

# initial render
render()

# ---------- layout ----------
header = pn.Row(
    pn.pane.Markdown("# 🎶 Music Rating Dashboard"),
    pn.Spacer(),
    sizing_mode="stretch_width",
)
controls = pn.Row(min_rating, topn, search, refresh, sizing_mode="stretch_width")

app = pn.Column(
    header,
    pn.pane.Markdown("_Data Analysis & Visualization_"),
    controls,
    metrics_md,
    bar_pane,
    hist_pane,
    pn.pane.Markdown("#### ℹ️ About\nThis dashboard visualizes song ratings from user votes."),
    table_w,
    sizing_mode="stretch_width",
)

# Expose for `panel serve`
app.servable()
