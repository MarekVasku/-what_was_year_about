"""
Gradio web UI for the annual "What Was [Year] About" music chart.

This module wires UI components to the core dashboard generator in `dashboard.create_dashboard`.
It intentionally keeps no business logic here; all computation, data access, and plotting
primitives live in `data_utils.py`, `load_data.py`, `visuals.py`, and `dashboard.py`.

Environment (optional):
- WEBHOOK_URL: If set (e.g., on Hugging Face Spaces), feedback is posted via webhook
- SMTP_EMAIL / SMTP_PASSWORD: If set locally, fallback SMTP is used for feedback

Safe to run locally: `python src/app_gradio.py`
"""


import gradio as gr

from config import (
    DEFAULT_YEAR,
    HEADER_IMAGE,
    RANKING_VIEW_CHOICES,
    RANKING_VIEW_MAPPING,
    SUPPORTED_YEARS,
)
from dashboard import create_dashboard
from feedback import FeedbackSubmitter
from settings import settings
from theme import CUSTOM_CSS, THEME

# ---------- Gradio UI (UI-only, imports functionality from modules) ----------
with gr.Blocks(title="What was the year about - music chart", theme=THEME, css=CUSTOM_CSS) as demo:
    # Hero section with optional image
    with gr.Column(elem_classes=["hero"]):
        gr.Image(value=str(HEADER_IMAGE), show_label=False, height=300)

        hero_title = gr.Markdown(f"# What Was {DEFAULT_YEAR} About")
        hero_subtitle = gr.Markdown("_Results of your's favourite yearly music chart_")

        # Spotify Playlist Embed (centered) - only for 2024
        spotify_embed = gr.HTML(
            """
            <div style="display: flex; justify-content: center; margin: 1rem 0;">
                <iframe data-testid="embed-iframe"
                        style="border-radius:12px;"
                        src="https://open.spotify.com/embed/playlist/3f8Wce2yeoEpOIGufXDYwD?utm_source=generator&theme=0"
                        width="100%"
                        height="352"
                        frameBorder="0"
                        allowfullscreen=""
                        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                        loading="lazy">
                </iframe>
            </div>
        """,
            visible=True,
        )
        spotify_note = gr.Markdown(
            (
                "Note: Some songs (BABYS IN A THUNDERCLOUD by Godspeed You! Black Emperor, Veneficium by Xiu Xiu) were removed from "
                "Spotify by artists protesting Spotify's policies about their investment in drones/military investments. "
                "Also F*ck ICE just for the sake."
            ),
            elem_classes=["model-note"],
            visible=True,
        )
        gr.Markdown(
            "<p style='font-size: 0.95rem; color: #ffffff !important; text-align: center; margin: 0.5rem 0 0.25rem;'>"
            "Please enter the same email prefix you used in the survey (before the @). This unlocks your personal insights."
            "</p>"
        )
        with gr.Row():
            year_selector = gr.Dropdown(
                label="Select Year", choices=SUPPORTED_YEARS, value=DEFAULT_YEAR, show_label=True, scale=1
            )
            email_input = gr.Textbox(
                label="Your email prefix", placeholder="e.g., macdemarco (without @gmail.com)", show_label=True, scale=2
            )
            refresh_btn = gr.Button("Refresh Data 🔄", variant="primary", scale=1)

    # Overview section (compact summary, no charts)
    with gr.Column(elem_classes=["overview-box"]):
        overview = gr.Markdown("")

    # Podium visualization
    gr.Markdown("## The Podium")
    gr.Markdown(
        "_The champions. Song winners of last years. The chosen ones. The songs that made you fill '10' without hesitation (or maybe they tied at 7.29, who knows)._"
    )
    podium_plot = gr.Plot()

    # Top 10 spotlight
    gr.Markdown("## Top 10 Spotlight")
    gr.Markdown(
        "_Because everyone loves a top 10 list. No matter how many songs were in the final playlist, everyone loves top 10s._"
    )
    top10_plot = gr.Plot()

    # Distribution charts side by side
    gr.Markdown("## Score Distributions")
    gr.Markdown(
        "_Ever wondered if everyone's just vibing around 7s or if there are actual opinions happening? And what about your voting patterns? These histograms know._"
    )
    with gr.Row():
        with gr.Column(scale=1):
            avg_dist_plot = gr.Plot()
        with gr.Column(scale=1):
            all_votes_plot = gr.Plot()

    # Full rankings
    gr.Markdown("## Complete Rankings")
    gr.Markdown(
        "_All the songs. Every single one. Ranked from 'meh' to 'oh my, life changing song I am hearing'. Switch views to see where you agree or disagree._"
    )
    with gr.Row():
        ranking_view = gr.Radio(
            label="View",
            choices=RANKING_VIEW_CHOICES,
            value="Final score + your score (overlay)",
        )
    main_plot = gr.Plot()

    # All songs table and user comparison
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Overall Rankings")
            all_songs_table = gr.Dataframe(headers=["Rank", "Song", "Average Score"], interactive=False, wrap=True)
        with gr.Column(scale=1):
            gr.Markdown("### Your Votes vs Average")
            user_comparison = gr.Dataframe(
                headers=["Rank", "Song", "Average Score", "Your Score", "Difference"], interactive=False, wrap=True
            )

    # New user-specific visualizations (only shown when user email is provided)
    gr.Markdown("## Your Personal Music Analysis")
    warning_personal = gr.Markdown(
        "<p style='color: #9333ea; font-size: 16px; font-weight: 600; margin-bottom: 10px;'>⚠️ To see your personalized insights, enter your email address above.</p>"
    )
    gr.Markdown(
        "This is where your music taste is analyzed (if you filled this year's survey). Enter your email above to unlock personalized insight."
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Biggest Disagreements")
            gr.Markdown("_Where you went full contrarian. Songs you loved that everyone not as much, or vice versa_")
            disagreements_plot = gr.Plot()
        with gr.Column(scale=1):
            gr.Markdown("### Your Top 10 vs Community")
            gr.Markdown("Left side: what the people chose. Right side: what you chose. The overlap reveals...")
            user_vs_top10_plot = gr.Plot()

    gr.Markdown("### Your Rating Pattern")
    warning_rating = gr.Markdown(
        "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>"
    )
    gr.Markdown(
        "_Are you a harsh critic handing out 3s like candy, or a generous soul showering 9s? This chart exposes your rating philosophy_"
    )
    rating_pattern_plot = gr.Plot()

    gr.Markdown("## Community Insights")
    gr.Markdown(
        "_Dive into the collective consciousness. See patterns, chaos, and who's secretly rating everything a 5._"
    )

    gr.Markdown("### All Votes Heatmap")
    gr.Markdown("_Voters are anonymized except you_")
    heatmap_plot = gr.Plot()

    gr.Markdown("### Most Polarizing Songs (Top 10)")
    gr.Markdown("_Where we all not met halfways. Maximum disagreement, maximum drama._")
    controversy_plot = gr.Plot()

    gr.Markdown("### Most Agreeable Songs (Top 10)")
    gr.Markdown("_Consensus achieved. Everyone basically gave these (almost) the same score._")
    agreeable_plot = gr.Plot()

    gr.Markdown("## Taste Similarity Map")
    gr.HTML(
        "<p style='font-size: 0.85rem; line-height: 1.4; color: #6b7280; font-style: italic; margin-bottom: 1rem;'>"
        "The 2D map uses an MDS projection over standardized voting patterns; closer dots ≈ more similar taste."
        "</p>"
    )

    gr.Markdown("### 2D Taste Map")
    gr.Markdown(
        "_Explore music taste similarities (anonymized). Currently far from being useful, will come handy with more voters (please vote next years!)._"
    )
    taste_map_plot = gr.Plot()

    # ========== STATE-OF-THE-ART 2026 VISUALIZATIONS ==========
    gr.Markdown("## 🎨 Advanced 2026 Visualizations")
    gr.Markdown(
        "_Cutting-edge data visualization techniques using the latest methods from 2026. "
        "Explore your music data in entirely new ways._"
    )

    gr.Markdown("### Sunburst Chart: Hierarchical Score Distribution")
    gr.Markdown(
        "_Modern circular hierarchy showing how songs distribute across score ranges. "
        "Click segments to zoom in and explore different score brackets._"
    )
    sunburst_plot = gr.Plot()

    gr.Markdown("### 3D Interactive Scatter: Score × Variance × Popularity")
    gr.Markdown(
        "_Explore songs in three-dimensional space with WebGL-powered smooth interactions. "
        "Each axis tells a different story: average score, vote variance, and popularity._"
    )
    scatter_3d_plot = gr.Plot()

    gr.Markdown("### Ridgeline Distribution: Top Songs Comparison")
    gr.Markdown(
        "_Elegant overlapping distributions (also known as joy plots) showing how votes "
        "distribute for top songs. Popularized by data visualization experts in the 2020s._"
    )
    ridgeline_plot = gr.Plot()

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Radial Ranking Chart")
            gr.Markdown(
                "_Circular layout inspired by modern infographic design. "
                "Rankings visualized in a visually striking radial pattern._"
            )
            radial_plot = gr.Plot()
        with gr.Column(scale=1):
            gr.Markdown("### Sankey Flow Diagram")
            gr.Markdown(
                "_Flow visualization showing how votes distribute from songs to score ranges. "
                "Perfect for understanding voting patterns at a glance._"
            )
            sankey_plot = gr.Plot()

    gr.Markdown("### Parallel Coordinates: Multi-Dimensional Analysis")
    gr.Markdown(
        "_State-of-the-art technique for comparing multiple metrics simultaneously. "
        "Draw patterns across rank, score, vote count, standard deviation, and score range._"
    )
    parallel_coords_plot = gr.Plot()

    gr.Markdown("## Your Music Taste Recommendations")
    warning_recommendations = gr.Markdown(
        "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above.</p>"
    )
    gr.Markdown(
        "_Generative AI (LLM) analyzes your favorites and suggests artists/genres to explore in 2025 - sometimes maybe good, sometimes maybe shit hallucination._"
    )
    recommendations_box = gr.Markdown("")

    def refresh_with_email(year, email_prefix, ranking_view_choice):
        """Wrapper to pass year, email and ranking view selector to create_dashboard."""
        view_key = RANKING_VIEW_MAPPING.get(ranking_view_choice, "overlay")
        dashboard_data = create_dashboard(email_prefix, ranking_view=view_key, year=year)
        results = dashboard_data.to_tuple()

        # Hide warnings if email is provided and has data
        has_data = email_prefix and email_prefix.strip() != ""
        warning_text = (
            ""
            if has_data
            else "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>"
        )

        # Update hero title based on year
        title = f"# What Was {year} About"

        # Show Spotify embed only for 2024
        show_spotify = year == 2024

        # Use gr.update to toggle visibility for HTML/Markdown components
        spotify_embed_update = gr.update(visible=show_spotify)
        spotify_note_update = gr.update(visible=show_spotify)

        return (title, *results, warning_text, warning_text, warning_text, spotify_embed_update, spotify_note_update)

    def refresh_main_chart_only(year, email_prefix, ranking_view_choice):
        """Refresh only the main chart when ranking view changes."""
        view_key = RANKING_VIEW_MAPPING.get(ranking_view_choice, "overlay")
        dashboard_data = create_dashboard(email_prefix, ranking_view=view_key, year=year)
        all_results = dashboard_data.to_tuple()
        return all_results[5]  # main_plot is the 6th item (index 5)

    # Wire up refresh with email
    all_outputs = [
        hero_title,  # Add hero_title as first output
        overview,
        podium_plot,
        top10_plot,
        avg_dist_plot,
        all_votes_plot,
        main_plot,
        all_songs_table,
        user_comparison,
        disagreements_plot,
        user_vs_top10_plot,
        heatmap_plot,
        controversy_plot,
        agreeable_plot,
        rating_pattern_plot,
        taste_map_plot,
        recommendations_box,
        # 2026 visualizations
        sunburst_plot,
        parallel_coords_plot,
        ridgeline_plot,
        scatter_3d_plot,
        sankey_plot,
        radial_plot,
        # Warnings
        warning_personal,
        warning_rating,
        warning_recommendations,
        spotify_embed,  # Add spotify visibility control
        spotify_note,  # Add spotify note visibility control
    ]

    refresh_btn.click(
        refresh_with_email,
        inputs=[year_selector, email_input, ranking_view],
        outputs=all_outputs,
    )

    # Auto-refresh only main chart when ranking view changes
    ranking_view.change(
        refresh_main_chart_only,
        inputs=[year_selector, email_input, ranking_view],
        outputs=main_plot,
    )

    # Email input triggers refresh too
    email_input.submit(
        refresh_with_email,
        inputs=[year_selector, email_input, ranking_view],
        outputs=all_outputs,
    )

    # Year selector triggers refresh too
    year_selector.change(
        refresh_with_email,
        inputs=[year_selector, email_input, ranking_view],
        outputs=all_outputs,
    )

    # Initial load with empty email and default year
    demo.load(
        lambda: (
            f"# What Was {DEFAULT_YEAR} About",
            *create_dashboard("", ranking_view="overlay", year=DEFAULT_YEAR).to_tuple(),
            "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>",
            "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>",
            "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>",
            gr.update(visible=True),
            gr.update(visible=True),
        ),
        inputs=None,
        outputs=all_outputs,
    )

    # Feedback section at the bottom
    gr.Markdown("---")
    gr.Markdown("## 💬 Your Input")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Suggest Songs for 2025")
            gr.Markdown("_Got songs you wanna share? Drop suggestions below. 2025 only_")
            song_suggestions = gr.Textbox(
                label="Your 2025 Song Suggestions",
                placeholder="Artist - Song Title\nArtist - Another Song\n...",
                lines=5,
                max_lines=10,
            )

        with gr.Column(scale=1):
            gr.Markdown("### Ideas for Improvement")
            gr.Markdown("_Missing a chart? Want a different visualization? Tell me what would make this better_")
            improvement_ideas = gr.Textbox(
                label="Your Ideas",
                placeholder="I think it would be cool if...",
                lines=5,
                max_lines=10,
            )

    submit_feedback_btn = gr.Button("Submit Feedback 📨", variant="primary", size="lg")
    feedback_status = gr.Markdown("")

    feedback_submitter = FeedbackSubmitter(
        webhook_url=settings.webhook_url,
        smtp_email=settings.smtp_email,
        smtp_password=settings.smtp_password,
    )

    def submit_feedback(email_prefix, songs, ideas):
        """Handle feedback submission with structured fallback logic."""
        if not songs.strip() and not ideas.strip():
            return "⚠️ Please fill in at least one field before submitting!"

        result = feedback_submitter.submit(email_prefix or "", songs, ideas)
        return result.message if result.message else "✅ **Thank you!** Your feedback has been saved."

    submit_feedback_btn.click(
        submit_feedback,
        inputs=[email_input, song_suggestions, improvement_ideas],
        outputs=feedback_status,
    )

    # Thank you note
    gr.Markdown("---")
    gr.HTML(
        "<p style='text-align: center; font-size: 0.9rem; color: #6b7280; line-height: 1.6;'>"
        "Thanks all for voting, listening, discussing, and generally giving a damn about music. "
        "I know I am obsessed with charts, music and data. Thanks for sharing this with me. Hope this is somehow useful or interesting. "
        "Let's just all share passion for music, talk about it and keep discovering. Here's to some great music ahead! "
        "See you next year. - MV"
        "</p>"
    )
    gr.Markdown("---")


if __name__ == "__main__":
    demo.launch(share=False)  # Set share=True for public link
