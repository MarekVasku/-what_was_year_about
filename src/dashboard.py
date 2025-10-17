from data_utils import get_data_cached
from llm_implementation import get_user_voting_insight
from visuals import (
    make_podium_chart,
    make_top_10_spotlight,
    make_main_chart,
    make_distribution_chart,
    make_all_votes_distribution,
)
import pandas as pd


def create_dashboard(user_email_prefix: str = ""):
    """Generate all dashboard components with optional user comparison."""
    df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, error, comparison = get_data_cached(user_email_prefix)
    
    if error:
        return (
            f"### ⚠️ Error Loading Data\n```\n{error}\n```",
            make_podium_chart(pd.DataFrame()), make_top_10_spotlight(pd.DataFrame()),
            make_distribution_chart(pd.DataFrame()), make_all_votes_distribution(pd.DataFrame()),
            make_main_chart(pd.DataFrame()), pd.DataFrame(), pd.DataFrame(),
        )
    
    if avg_scores.empty:
        return (
            "### 📊 No Data Yet\nClick refresh to load voting results.",
            make_podium_chart(pd.DataFrame()), make_top_10_spotlight(pd.DataFrame()),
            make_distribution_chart(pd.DataFrame()), make_all_votes_distribution(pd.DataFrame()),
            make_main_chart(pd.DataFrame()), pd.DataFrame(),
        )
    
    # --- Overview respecting ties and listing all tied songs ---
    top1 = avg_scores[avg_scores['Rank'] == 1]
    top2 = avg_scores[avg_scores['Rank'] == 2]
    top3 = avg_scores[avg_scores['Rank'] == 3]

    def place_line(place_df, medal):
        if place_df.empty:
            return f"{medal} —"
        items = [
            f"{row['Song']} ({row['Average Score']:.2f})"
            for _, row in place_df.iterrows()
        ]
        return f"{medal} " + " • ".join(items)

    # Winner display (all rank-1 songs listed)
    if not top1.empty:
        winners = " | ".join([f"{row['Song']}" for _, row in top1.iterrows()])
        winner_display = f"{winners} — **{top1.iloc[0]['Average Score']:.2f}**"
    else:
        winner_display = "—"

    top3_line = "  •  ".join([
        place_line(top1, "🥇"),
        place_line(top2, "🥈"),
        place_line(top3, "🥉"),
    ])


    overview = f"""### Winner
{winner_display}

Stats: {total_votes} votes  •  {total_songs} songs  •  Average: {avg_of_avgs:.2f}

### Top 3
{top3_line}
"""
    
    # Generate charts
    podium_chart = make_podium_chart(avg_scores)
    top10_chart = make_top_10_spotlight(avg_scores)
    main_chart = make_main_chart(avg_scores, comparison if comparison is not None else None)
    dist_chart = make_distribution_chart(avg_scores)
    all_votes_chart = make_all_votes_distribution(df_raw)
    
    # All songs table (rounded to 2 decimals)
    all_songs_table = avg_scores[['Rank', 'Song', 'Average Score']].copy()
    all_songs_table['Average Score'] = all_songs_table['Average Score'].round(2)
    
    # User comparison section and LLM insight
    user_comparison = comparison
    if comparison is not None and not comparison.empty:
        comparison_display = comparison.round(2)
        # Get LLM insight about voting patterns
        insight = get_user_voting_insight(comparison)
        if insight:
            overview = overview + f"\n\n### 🎯 Your Voting Pattern\n{insight}"
    else:
        comparison_display = pd.DataFrame()
    
    return (
        overview,
        podium_chart,
        top10_chart,
        dist_chart,
        all_votes_chart,
        main_chart,
        all_songs_table,
        comparison_display
    )
import pandas as pd
import plotly.express as px
from nicegui import ui

# Playing around and experimenting with the NiceGUI framework


def show_dashboard(df):
    # Identify song columns (skip first columns like timestamp & email)
    song_columns = df.columns[2:]

    # Convert song rating columns to numeric
    df[song_columns] = df[song_columns].apply(pd.to_numeric, errors='coerce')

    # Compute mean scores, dropping NaNs
    avg_scores = df[song_columns].mean().dropna().reset_index()
    avg_scores.columns = ["Song", "Average Score"]

    # Remove songs with 0 ratings
    avg_scores = avg_scores[avg_scores["Average Score"] > 0].copy()

    # Sort by average score
    sorted_data = avg_scores.sort_values(by="Average Score", ascending=True)

    # **Dashboard Header**
    with ui.row().classes("w-full items-center justify-between bg-gray-900 text-white p-5 shadow-lg"):
        ui.label("Music Rating Dashboard").classes("text-3xl font-bold")
        ui.label("Data Analysis & Visualization").classes("text-lg")

    # **Key Metrics Section**
    with ui.row().classes("w-full bg-gray-100 p-5 shadow-sm"):
        with ui.column():
            ui.label(f"Total Votes: {df.shape[0]}").classes("text-2xl font-semibold")
            ui.label(f"Highest Rated: {sorted_data.iloc[-1]['Song']} ({sorted_data.iloc[-1]['Average Score']:.2f})").classes("text-lg text-gray-600")
            ui.label(f"Average Rating: {sorted_data['Average Score'].mean():.2f}").classes("text-lg text-gray-600")

    # **Dynamic Charts Section**
    with ui.row().classes("w-full justify-around p-5"):
        chart_area = ui.column().classes("w-2/3 bg-white p-4 shadow rounded-lg")

    def update_chart():
        filtered_data = sorted_data[
            sorted_data["Average Score"] >= rating_threshold.value
        ].sort_values(by="Average Score", ascending=True)

        fig = px.bar(
            filtered_data,
            x="Average Score",
            y="Song",
            orientation="h",
            title="Top Rated Songs",
            text="Average Score",
            color="Average Score",
            color_continuous_scale="darkmint",  # ✅ More elegant color scheme
        )

        fig.update_traces(textposition="outside")

        # ✅ Modern Styling
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis_title="Average Score",
            yaxis_title="Songs",
            title_x=0.5,
            width=1200,
            height=600,
        )

        plot.figure = fig
        plot.update()

    # **Rating Threshold & Filter**
    with ui.row().classes("w-full items-center p-4 bg-gray-200"):
        ui.label("Minimum Rating Filter:").classes("text-lg")
        rating_threshold = ui.slider(
            min=sorted_data["Average Score"].min(),
            max=sorted_data["Average Score"].max(),
            value=sorted_data["Average Score"].min(),
            step=0.1,
        ).bind_value(update_chart)

    # **Search Bar**
    with ui.row().classes("w-full p-4 bg-gray-100"):
        search_input = ui.input("Search for a song").classes("w-1/3 p-2 border rounded")
        def search_song():
            search_term = search_input.value.lower()
            filtered_data = sorted_data[
                sorted_data["Song"].str.lower().str.contains(search_term, na=False)
            ]
            if filtered_data.empty:
                ui.notify("No matching songs found!")
            else:
                update_chart()

        ui.button("Search", on_click=search_song).classes("bg-blue-500 text-white p-2 rounded")

    # **Chart Display**
    empty_data = pd.DataFrame({'Song': [], 'Average Score': []})  # Empty DataFrame
    fig = px.bar(empty_data, x="Average Score", y="Song")  # Initialize empty figure
    plot = ui.plotly(fig)
    update_chart()

    # **Distribution Chart**
    with chart_area:
        fig_hist = px.histogram(
            sorted_data,
            x="Average Score",
            nbins=10,
            title="Distribution of Ratings",
            color_discrete_sequence=["#2C3E50"],  # ✅ Professional dark blue tone
        )

        fig_hist.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            title_x=0.5,
            width=1200,
            height=400,
        )

        ui.plotly(fig_hist)

    # **About Section**
    with ui.row().classes("w-full p-5 bg-gray-50"):
        ui.label("About This Dashboard").classes("text-2xl font-bold")
        ui.label(
            "This dashboard visualizes song ratings based on user votes. "
            "Use the interactive filters and search bar to explore the data."
        ).classes("text-lg text-gray-600")
