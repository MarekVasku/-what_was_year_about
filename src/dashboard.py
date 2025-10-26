import pandas as pd

from data_utils import create_2d_taste_map, get_data_cached
from llm_implementation import (
    MODEL_ANALYSIS,
    MODEL_JSON,
    generate_recommendations,
    get_user_voting_insight,
)
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


def create_dashboard(user_email_prefix: str = "", ranking_view: str = "overlay"):
    """Generate all dashboard components with optional user comparison.

    Args:
        user_email_prefix: user identifier (prefix before @) to enable personal insights; empty string disables them
        ranking_view: one of "overlay" (avg + your scores), "user" (only your scores), or "average" (only group average)

    Returns:
        Tuple in the following strict order expected by the Gradio UI wiring:
        (
            overview_markdown: str,
            podium_chart: Figure,
            top10_chart: Figure,
            dist_chart: Figure,
            all_votes_chart: Figure,
            main_chart: Figure,
            all_songs_table: DataFrame,
            comparison_display: DataFrame,
            disagreements_chart: Figure,
            user_vs_top10_chart: Figure,
            heatmap_chart: Figure,
            controversy_chart: Figure,
            agreeable_chart: Figure,
            rating_pattern_chart: Figure,
            taste_map_chart: Figure,
            recommendations_display: str,
        )
    """
    df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, error, comparison = get_data_cached(user_email_prefix)

    empty_fig = make_podium_chart(pd.DataFrame())
    if error:
        return (
            f"### ⚠️ Error Loading Data\n```\n{error}\n```",
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            pd.DataFrame(), pd.DataFrame(),
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            empty_fig,
            "",  # recommendations_display
        )

    if avg_scores.empty:
        empty_fig = make_podium_chart(pd.DataFrame())
        return (
            "### 📊 No Data Yet\nClick refresh to load voting results.",
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            pd.DataFrame(), pd.DataFrame(),
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            empty_fig,
            "",  # recommendations_display
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
        winner_display = f"{winners} — {top1.iloc[0]['Average Score']:.2f}"
    else:
        winner_display = "—"

    top3_lines = [
        place_line(top1, "🥇"),
        place_line(top2, "🥈"),
        place_line(top3, "🥉"),
    ]


    overview = f"""### Winner
{winner_display}

Stats: {total_votes} votes  •  {total_songs} songs  •  Average: {avg_of_avgs:.2f}

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
    all_songs_table = avg_scores[avg_scores['Average Score'] > 0][['Rank', 'Song', 'Average Score']].copy()
    all_songs_table['Average Score'] = all_songs_table['Average Score'].round(2)

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
            sorted_comparison = comparison.sort_values(by='Your Score', ascending=False)
            top5_songs = sorted_comparison.head(5)['Song'].tolist()
            bottom5_songs = sorted_comparison.tail(5)['Song'].tolist()

            recommendations = generate_recommendations(top5_songs, bottom5_songs, n=5)

            # Format recommendations for display (artist/genre focused)
            if recommendations and len(recommendations) > 0:
                rec_lines = []
                for i, rec in enumerate(recommendations, 1):
                    artist_or_genre = rec.get('song', 'Unknown')  # 'song' field contains artist/genre
                    reason = rec.get('reason', 'No reason provided')
                    rec_lines.append(f"**{i}. {artist_or_genre}**\n   _{reason}_")

                recommendations_display = "\n\n".join(rec_lines)
                recommendations_display += (
                    f"\n\n<span class='model-note-white'>Generated with <code>{MODEL_JSON}</code> on Groq</span>"
                )
        except Exception as e:
            recommendations_display = f"_Could not generate recommendations: {str(e)}_"
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
        comparison_display,
        disagreements_chart,
        user_vs_top10_chart,
        heatmap_chart,
        controversy_chart,
        agreeable_chart,
        rating_pattern_chart,
        taste_map_chart,
        recommendations_display,
    )

