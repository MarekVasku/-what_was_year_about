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
            "Enter your email prefix (the part before @) to unlock personalized insights and comparisons."
            "</p>"
        )
        with gr.Row():
            year_selector = gr.Dropdown(
                label="Select Year",
                choices=SUPPORTED_YEARS,
                value=DEFAULT_YEAR,
                show_label=True,
                scale=1,
                info="Choose which year's results to view",
            )
            email_input = gr.Textbox(
                label="Your email prefix",
                placeholder="e.g., macdemarco (without @gmail.com)",
                show_label=True,
                scale=2,
                info="Optional - only if you participated in the survey",
            )
            refresh_btn = gr.Button("Refresh Data 🔄", variant="primary", scale=1)

    # Overview section (compact summary, no charts)
    with gr.Column(elem_classes=["overview-box"]):
        overview = gr.Markdown("")

    # Podium visualization
    gr.Markdown("## 🏆 The Podium")
    gr.Markdown(
        "_The champions. The songs that won over hearts and ears. These are the ones that made people click '10' without hesitation._"
    )
    podium_plot = gr.Plot()

    # Top 10 spotlight
    gr.Markdown("## ⭐ Top 10 Spotlight")
    gr.Markdown("_The cream of the crop. These songs rose to the top and became the year's favorites._")
    top10_plot = gr.Plot()

    # Distribution charts side by side
    gr.Markdown("## 📊 Score Distributions")
    gr.Markdown(
        "_How did everyone rate the songs? Are most scores clustering around 7, or is there a wide variety of opinions? These charts reveal the patterns._"
    )
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("**Average Score Distribution**")
            avg_dist_plot = gr.Plot()
        with gr.Column(scale=1):
            gr.Markdown("**All Individual Votes**")
            all_votes_plot = gr.Plot()

    # Full rankings
    gr.Markdown("## 📋 Complete Rankings")
    gr.Markdown(
        "_Every song ranked from highest to lowest. Switch between views to compare your scores with the community average._"
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
    gr.Markdown("## 🎯 Your Personal Music Analysis")
    warning_personal = gr.Markdown(
        "<p style='color: #9333ea; font-size: 16px; font-weight: 600; margin-bottom: 10px;'>⚠️ Enter your email prefix above to unlock personalized insights.</p>"
    )
    gr.Markdown(
        "_Deep dive into your unique music taste based on your survey responses. See how your preferences compare to the community._"
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🎭 Biggest Disagreements")
            gr.Markdown("_Songs where your opinion differs most from the crowd - your hidden gems or unpopular picks._")
            disagreements_plot = gr.Plot()
        with gr.Column(scale=1):
            gr.Markdown("### 🔄 Your Top 10 vs Community")
            gr.Markdown("_Left: Community favorites. Right: Your favorites. How much overlap do you have?_")
            user_vs_top10_plot = gr.Plot()

    gr.Markdown("### 📈 Your Rating Pattern")
    warning_rating = gr.Markdown(
        "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ Enter your email prefix above to see your rating pattern.</p>"
    )
    gr.Markdown("_Are you a generous scorer or a tough critic? This reveals your rating tendencies._")
    rating_pattern_plot = gr.Plot()

    gr.Markdown("## 👥 Community Insights")
    gr.Markdown("_Explore how the community voted as a whole. Discover patterns, agreements, and controversies._")

    gr.Markdown("### 🗺️ All Votes Heatmap")
    gr.Markdown("_Visual representation of all votes. You'll be highlighted if you enter your email._")
    heatmap_plot = gr.Plot()

    gr.Markdown("### ⚡ Most Polarizing Songs (Top 10)")
    gr.Markdown("_Maximum disagreement. These songs split the community - some loved them, some didn't._")
    controversy_plot = gr.Plot()

    gr.Markdown("### 🤝 Most Agreeable Songs (Top 10)")
    gr.Markdown("_Maximum consensus. Everyone rated these songs similarly._")
    agreeable_plot = gr.Plot()

    gr.Markdown("## 🎨 Taste Similarity Map")
    gr.HTML(
        "<p style='font-size: 0.85rem; line-height: 1.4; color: #6b7280; font-style: italic; margin-bottom: 1rem;'>"
        "This 2D visualization uses MDS (Multidimensional Scaling) to show voter similarity. "
        "Voters with similar tastes appear closer together."
        "</p>"
    )

    gr.Markdown("### 🗺️ 2D Taste Map")
    gr.Markdown(
        "_Visual clustering of voters by taste similarity. As more people participate, patterns become clearer!_"
    )
    taste_map_plot = gr.Plot()

    gr.Markdown("## 🎵 Your Music Taste Recommendations")
    warning_recommendations = gr.Markdown(
        "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ Enter your email prefix above to unlock personalized insights.</p>"
    )
    gr.Markdown(
        "_AI-powered recommendations based on your top-rated songs. "
        "Discover new artists and genres that match your taste._"
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
            else "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ Enter your email prefix above to unlock personalized insights.</p>"
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
            "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ Enter your email prefix above to unlock personalized insights.</p>",
            "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ Enter your email prefix above to unlock personalized insights.</p>",
            "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ Enter your email prefix above to unlock personalized insights.</p>",
            gr.update(visible=True),
            gr.update(visible=True),
        ),
        inputs=None,
        outputs=all_outputs,
    )

    # Feedback section at the bottom
    gr.Markdown("---")
    gr.Markdown("## 💬 Share Your Feedback")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🎵 Suggest Songs for 2025")
            gr.Markdown("_Know some amazing tracks that should be on next year's list? Share them here!_")
            song_suggestions = gr.Textbox(
                label="Your 2025 Song Suggestions",
                placeholder="Artist - Song Title\nAnother Artist - Another Song\n...",
                lines=5,
                max_lines=10,
            )

        with gr.Column(scale=1):
            gr.Markdown("### 💡 Ideas for Improvement")
            gr.Markdown("_Have suggestions for new features or visualizations? Let us know what would make this better!_")
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
