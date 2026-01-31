import pandas as pd
import plotly.express as px  # noqa: F401
from nicegui import ui  # noqa: F401

from data_utils import create_2d_taste_map, get_data_cached
from llm_implementation import (
    MODEL_ANALYSIS,
    MODEL_JSON,
    generate_recommendations,
    get_user_voting_insight,
)
from models import DashboardData
from visuals import (
    make_2d_taste_map_chart,
    make_all_votes_distribution,
    make_biggest_disagreements_chart,
    make_controversy_chart,
    make_distribution_chart,
    make_main_chart,
    make_main_chart_user_only,
    make_most_agreeable_chart,
    make_podium_chart,
    make_top_10_spotlight,
    make_user_rating_pattern,
    make_user_vs_community_top10,
    make_voting_heatmap,
)


def create_dashboard(user_email_prefix: str = "", ranking_view: str = "overlay", year: int = 2024):
    """Generate all dashboard components with optional user comparison.

    Args:
        user_email_prefix: User's email prefix for personalized data
        ranking_view: one of "overlay" (avg + your scores), "user" (only your scores), or "average" (only group average)
        year: Year to display data for (2019, 2023, or 2024)
    """
    df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, error, comparison = get_data_cached(
        user_email_prefix, year
    )

    empty_fig = make_podium_chart(pd.DataFrame())
    if error:
        return DashboardData(
            overview=f"### ⚠️ Error Loading Data\n```\n{error}\n```",
            total_votes=0,
            total_songs=0,
            avg_of_avgs=0.0,
            error_message=error,
            podium_plot=empty_fig,
            top10_plot=empty_fig,
            distribution_plot=empty_fig,
            all_votes_plot=empty_fig,
            main_plot=empty_fig,
            all_songs_table=pd.DataFrame(),
            user_comparison_table=pd.DataFrame(),
            disagreements_plot=empty_fig,
            user_vs_top10_plot=empty_fig,
            heatmap_plot=empty_fig,
            controversy_plot=empty_fig,
            agreeable_plot=empty_fig,
            rating_pattern_plot=empty_fig,
            taste_map_plot=empty_fig,
            recommendations_display="",
        )

    if avg_scores.empty:
        empty_fig = make_podium_chart(pd.DataFrame())
        return DashboardData(
            overview="### 📊 No Data Yet\nClick refresh to load voting results.",
            total_votes=0,
            total_songs=0,
            avg_of_avgs=0.0,
            podium_plot=empty_fig,
            top10_plot=empty_fig,
            distribution_plot=empty_fig,
            all_votes_plot=empty_fig,
            main_plot=empty_fig,
            all_songs_table=pd.DataFrame(),
            user_comparison_table=pd.DataFrame(),
            disagreements_plot=empty_fig,
            user_vs_top10_plot=empty_fig,
            heatmap_plot=empty_fig,
            controversy_plot=empty_fig,
            agreeable_plot=empty_fig,
            rating_pattern_plot=empty_fig,
            taste_map_plot=empty_fig,
            recommendations_display="",
        )

    # --- Overview respecting ties and listing all tied songs ---
    top1 = avg_scores[avg_scores["Rank"] == 1]
    top2 = avg_scores[avg_scores["Rank"] == 2]
    top3 = avg_scores[avg_scores["Rank"] == 3]

    def place_line(place_df, medal):
        if place_df.empty:
            return f"{medal} —"
        items = [f"{row['Song']} ({row['Average Score']:.2f})" for _, row in place_df.iterrows()]
        return f"{medal} " + " • ".join(items)

    # Winner display (all rank-1 songs listed)
    if not top1.empty:
        winners = " | ".join([f"{row['Song']}" for _, row in top1.iterrows()])
        winner_display = f"{winners} — {top1.iloc[0]['Average Score']:.2f}"
    else:
        winner_display = "—"

    # Add user message if applicable
    user_not_found_message = ""
    if user_email_prefix and (comparison is None or comparison.empty):
        user_not_found_message = " (user not found)"

    top3_lines = [
        place_line(top1, "🥇"),
        place_line(top2, "🥈"),
        place_line(top3, "🥉"),
    ]

    overview = f"""### Winner
{winner_display}

Stats: {total_votes} votes  •  {total_songs} songs  •  Average: {avg_of_avgs:.2f}{user_not_found_message}

### Top 3

{top3_lines[0]}
{top3_lines[1]}
{top3_lines[2]}
"""

    # Generate charts
    podium_chart = make_podium_chart(avg_scores)
    top10_chart = make_top_10_spotlight(avg_scores)
    # Choose which main chart to show per requested view
    view = (ranking_view or "overlay").lower()
    if view == "user" and comparison is not None and not comparison.empty:
        main_chart = make_main_chart_user_only(comparison)
    elif view == "average":
        main_chart = make_main_chart(avg_scores, None)
    else:  # overlay (default)
        main_chart = make_main_chart(avg_scores, comparison if comparison is not None else None)
    dist_chart = make_distribution_chart(avg_scores)
    all_votes_chart = make_all_votes_distribution(df_raw)

    # All songs table (rounded to 2 decimals, exclude songs with no votes)
    all_songs_table = avg_scores[avg_scores["Average Score"] > 0][["Rank", "Song", "Average Score"]].copy()
    all_songs_table["Average Score"] = all_songs_table["Average Score"].round(2)

    # User-specific visualizations
    disagreements_chart = make_podium_chart(pd.DataFrame())  # empty default
    user_vs_top10_chart = make_podium_chart(pd.DataFrame())
    heatmap_chart = make_voting_heatmap(df_raw, user_email_prefix)
    controversy_chart = make_controversy_chart(df_raw, avg_scores)
    agreeable_chart = make_most_agreeable_chart(df_raw, avg_scores)
    rating_pattern_chart = make_podium_chart(pd.DataFrame())

    # Clustering visualizations
    taste_map_chart = make_2d_taste_map_chart(create_2d_taste_map(df_raw, user_email_prefix))

    # User comparison section and LLM insight
    recommendations_display = ""

    if comparison is not None and not comparison.empty:
        comparison_display = comparison.round(2)
        # Get LLM insight about voting patterns
        insight = get_user_voting_insight(comparison)
        if insight:
            # Plain-size label, plus model info note
            overview = overview + (
                f"\n\n**Your Voting Pattern (LLM-generated):**\n{insight}\n"
                f"\n<span class='model-note'>Generated with <code>{MODEL_ANALYSIS}</code> on Groq</span>"
            )

        # Generate user-specific charts
        disagreements_chart = make_biggest_disagreements_chart(comparison)
        user_vs_top10_chart = make_user_vs_community_top10(comparison, avg_scores)
        rating_pattern_chart = make_user_rating_pattern(comparison, df_raw)

        # Generate artist/genre recommendations based on taste
        try:
            # Get top 5 and bottom 5 songs based on user's ratings
            sorted_comparison = comparison.sort_values(by="Your Score", ascending=False)
            top5_songs = sorted_comparison.head(5)["Song"].tolist()
            bottom5_songs = sorted_comparison.tail(5)["Song"].tolist()

            recommendations = generate_recommendations(top5_songs, bottom5_songs, n=5)

            # Format recommendations for display (artist/genre focused)
            if recommendations and len(recommendations) > 0:
                rec_lines = []
                for i, rec in enumerate(recommendations, 1):
                    artist_or_genre = rec.get("song", "Unknown")  # 'song' field contains artist/genre
                    reason = rec.get("reason", "No reason provided")
                    rec_lines.append(f"**{i}. {artist_or_genre}**\n   _{reason}_")

                recommendations_display = "\n\n".join(rec_lines)
                recommendations_display += (
                    f"\n\n<span class='model-note-white'>Generated with <code>{MODEL_JSON}</code> on Groq</span>"
                )
        except Exception as e:
            recommendations_display = f"_Could not generate recommendations: {str(e)}_"
    else:
        comparison_display = pd.DataFrame()
        # If user provided an email but no votes found, show message
        if user_email_prefix:
            recommendations_display = f"⚠️ **No votes found for `{user_email_prefix}`**\n\nPlease check your email prefix (the part before @)."

    return DashboardData(
        overview=overview,
        total_votes=total_votes,
        total_songs=total_songs,
        avg_of_avgs=avg_of_avgs,
        podium_plot=podium_chart,
        top10_plot=top10_chart,
        distribution_plot=dist_chart,
        all_votes_plot=all_votes_chart,
        main_plot=main_chart,
        all_songs_table=all_songs_table,
        user_comparison_table=comparison_display,
        disagreements_plot=disagreements_chart,
        user_vs_top10_plot=user_vs_top10_chart,
        heatmap_plot=heatmap_chart,
        controversy_plot=controversy_chart,
        agreeable_plot=agreeable_chart,
        rating_pattern_plot=rating_pattern_chart,
        taste_map_plot=taste_map_chart,
        recommendations_display=recommendations_display,
    )


# Playing around and experimenting with the NiceGUI framework


def show_dashboard(df):
    # Identify song columns (skip first columns like timestamp & email)
    song_columns = df.columns[2:]

    # Convert song rating columns to numeric
    df[song_columns] = df[song_columns].apply(pd.to_numeric, errors="coerce")

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
            ui.label(
                f"Highest Rated: {sorted_data.iloc[-1]['Song']} ({sorted_data.iloc[-1]['Average Score']:.2f})"
            ).classes("text-lg text-gray-600")
            ui.label(f"Average Rating: {sorted_data['Average Score'].mean():.2f}").classes("text-lg text-gray-600")

    # **Dynamic Charts Section**
    with ui.row().classes("w-full justify-around p-5"):
        chart_area = ui.column().classes("w-2/3 bg-white p-4 shadow rounded-lg")

    def update_chart():
        filtered_data = sorted_data[sorted_data["Average Score"] >= rating_threshold.value].sort_values(
            by="Average Score", ascending=True
        )

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
            filtered_data = sorted_data[sorted_data["Song"].str.lower().str.contains(search_term, na=False)]
            if filtered_data.empty:
                ui.notify("No matching songs found!")
            else:
                update_chart()

        ui.button("Search", on_click=search_song).classes("bg-blue-500 text-white p-2 rounded")

    # **Chart Display**
    empty_data = pd.DataFrame({"Song": [], "Average Score": []})  # Empty DataFrame
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
