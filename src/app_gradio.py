import pandas as pd
import plotly.express as px
import gradio as gr
from functools import lru_cache
from load_data import fetch_data

# ---------- Data prep ----------
def compute_scores(df: pd.DataFrame):
    # Identify song columns (skip first columns like timestamp & email)
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
    # Remove songs with 0 ratings
    avg_scores = avg_scores[avg_scores["Average Score"] > 0].copy()
    # Sort ascending so bars plot from low → high (same as your NiceGUI)
    avg_scores = avg_scores.sort_values("Average Score", ascending=True).reset_index(drop=True)
    return df, avg_scores

@lru_cache(maxsize=1)
def get_data_cached():
    df = fetch_data()
    df_raw, avg_scores = compute_scores(df)
    # Metrics
    total_votes = len(df_raw) if df_raw is not None else 0
    highest_txt = "N/A"
    avg_of_avgs = float("nan")
    if not avg_scores.empty:
        top = avg_scores.iloc[-1]
        highest_txt = f"{top['Song']} ({top['Average Score']:.2f})"
        avg_of_avgs = avg_scores["Average Score"].mean()
    return df_raw, avg_scores, total_votes, highest_txt, avg_of_avgs

def refresh_data():
    get_data_cached.cache_clear()
    return update(min_rating=None, search="", topn=None)

# ---------- UI logic ----------
def filter_df(avg_scores: pd.DataFrame, min_rating, search, topn):
    q = avg_scores.copy()
    if min_rating is not None:
        q = q[q["Average Score"] >= float(min_rating)]
    if search:
        s = str(search).lower()
        q = q[q["Song"].str.lower().str.contains(s, na=False)]
    if topn is not None and int(topn) > 0:
        q = q.sort_values("Average Score", ascending=False).head(int(topn))
        q = q.sort_values("Average Score", ascending=True)
    return q.reset_index(drop=True)

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

def update(min_rating, search, topn):
    df_raw, avg_scores, total_votes, highest_txt, avg_of_avgs = get_data_cached()

    # Defaults for first render
    if avg_scores.empty:
        metrics_md = "### 📊 Key Metrics\n_No data yet._"
        empty = avg_scores.head(0)
        return (
            metrics_md,
            empty,
            make_bar(empty),
            make_hist(empty),
            0.0,
            0 if empty.empty else min(20, len(avg_scores)),
        )

    if min_rating is None:
        min_rating = float(avg_scores["Average Score"].min())
    if topn is None:
        topn = min(20, len(avg_scores))

    filtered = filter_df(avg_scores, min_rating, search, topn)

    metrics_md = f"""### 📊 Key Metrics
- **Total Votes**: {total_votes}
- **Highest Rated**: {highest_txt}
- **Average of Averages**: {avg_of_avgs:.2f}
"""

    bar_fig = make_bar(filtered if not filtered.empty else avg_scores.head(0))
    hist_fig = make_hist(avg_scores)
    table_df = filtered[["Song", "Average Score"]].copy()

    return (
        metrics_md,
        table_df,
        bar_fig,
        hist_fig,
        float(min_rating),
        int(topn),
    )

# ---------- Gradio UI ----------
with gr.Blocks(title="What Was Year About - 2024 Music Votes") as demo:
    gr.Markdown("# 🎶 Music Rating Dashboard\n_Data Analysis & Visualization_")

    # Controls
    with gr.Row():
        min_rating = gr.Slider(minimum=0.0, maximum=10.0, value=0.0, step=0.1, label="Minimum Rating")
        topn = gr.Slider(minimum=1, maximum=200, value=20, step=1, label="Top N")
        search = gr.Textbox("", label="Search for a song", placeholder="Type part of a title…")
        refresh_btn = gr.Button("🔄 Refresh")

    # Outputs
    metrics = gr.Markdown()
    table = gr.Dataframe(headers=["Song", "Average Score"], interactive=False, max_height=360)
    bar_plot = gr.Plot()
    hist_plot = gr.Plot()

    # Wire interactions
    for ctrl in (min_rating, topn, search):
        ctrl.change(
            update,
            inputs=[min_rating, search, topn],
            outputs=[metrics, table, bar_plot, hist_plot, min_rating, topn],
        )
    refresh_btn.click(
        refresh_data,
        inputs=None,
        outputs=[metrics, table, bar_plot, hist_plot, min_rating, topn],
    )

    # Initial render with real ranges
    _df, _avg, _total, _highest, _avgall = get_data_cached()
    if not _avg.empty:
        min_rating.minimum = float(_avg["Average Score"].min())
        min_rating.maximum = float(min(10.0, _avg["Average Score"].max()))
        topn.maximum = int(len(_avg))

    init_vals = update(
        float(min_rating.value or (float(_avg["Average Score"].min()) if not _avg.empty else 0.0)),
        "",
        int(topn.value or (min(20, len(_avg)) if not _avg.empty else 0)),
    )
    metrics.value, table.value, bar_plot.value, hist_plot.value, min_rating.value, topn.value = init_vals

if __name__ == "__main__":
    demo.launch()  # add share=True to get a public link
