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
from gradio import themes
from pathlib import Path
from dashboard import create_dashboard
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# ---------- Gradio UI (UI-only, imports functionality from modules) ----------
theme = themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    neutral_hue="slate",
    font=themes.GoogleFont("Inter"),
).set(
    body_background_fill="*neutral_950",
    block_title_text_weight="600",
)

ROOT = Path(__file__).resolve().parent.parent
HEADER = ROOT / "static" / "header.png"

# Reusable HTML snippets (kept as constants to avoid duplication)
WARNING_HTML = (
    "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>"
    "⚠️ To see your personalized insights, enter your email address above"
    "</p>"
)

CUSTOM_CSS = """
    .gradio-container {max-width: 1400px !important; margin: 0 auto !important; padding: 0 1rem !important;}
    .hero {text-align: center; padding: 2rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           border-radius: 12px; margin-bottom: 2rem; color: white;}
    .hero h1 {color: white !important; font-size: 2.5rem; margin-bottom: 0.5rem;}
    .hero p {font-size: 1.1rem; opacity: 0.9;}
    /* Force email instruction to be white */
    .hero p[style*="font-size: 0.95rem"] {color: #ffffff !important;}
    /* Winner + Top 3 panel should stay light */
    .overview-box {background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 2rem;
                  color: #111827 !important; line-height: 1.6 !important; font-size: 1.1rem !important;}
    .overview-box h1, .overview-box h2, .overview-box h3 {color: #111827 !important;}
    .overview-box h3 {font-size: 1.6rem !important; margin-top: 1.5rem !important; margin-bottom: 0.75rem !important;
                     font-weight: 600 !important; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem;}
    .overview-box p {font-size: 1.1rem !important; color: #111827 !important; margin-bottom: 1rem !important;}
    /* Force inline elements to dark color inside the light panel */
    .overview-box strong, .overview-box em, .overview-box b, .overview-box i,
    .overview-box span, .overview-box li, .overview-box a { color: #111827 !important; }
    /* Tiny model info note */
    .model-note { font-size: 0.8rem !important; color: #0d1b2a !important; display: block; text-align: center !important; margin-top: -5px !important; }
    /* Ensure override inside hero where base color is white */
    .hero .model-note, .hero .model-note p { font-size: 0.8rem !important; color: #0d1b2a !important; }
    .overview-box .model-note { color: #0d1b2a !important; }
    .stats-line {font-size: 1rem !important; color: #6b7280 !important; margin: 0.5rem 0 !important;}
    /* Subtle text that adapts to backgrounds */
    .subtle-info { font-size: 0.85rem !important; line-height: 1.4 !important; color: #93c5fd !important; font-style: italic !important; }
    .thank-you-note { text-align: center !important; font-size: 0.9rem !important; color: #93c5fd !important; line-height: 1.6 !important; }
    /* White text for model notes on dark backgrounds (recommendations section) */
    .model-note-white { font-size: 0.8rem !important; color: #ffffff !important; display: block; text-align: center !important; margin-top: 0.5rem !important; opacity: 0.8; }
    
    /* Mobile responsive styles */
    @media (max-width: 768px) {
        .gradio-container {padding: 0 0.5rem !important;}
        .hero {padding: 1.5rem 0.75rem; margin-bottom: 1.5rem; border-radius: 8px;}
        .hero h1 {font-size: 1.75rem !important;}
        .hero p {font-size: 0.95rem !important;}
        .overview-box {padding: 1.25rem; font-size: 1rem !important;}
        .overview-box h3 {font-size: 1.3rem !important; margin-top: 1rem !important;}
        .overview-box p {font-size: 1rem !important;}
        .stats-line {font-size: 0.9rem !important;}
        /* Make tables scrollable on mobile */
        .dataframe {overflow-x: auto !important; font-size: 0.85rem !important;}
        /* Adjust iframe for mobile */
        iframe[data-testid="embed-iframe"] {height: 280px !important;}
    }
    
    @media (max-width: 480px) {
        .hero {padding: 1rem 0.5rem;}
        .hero h1 {font-size: 1.5rem !important;}
        .hero p {font-size: 0.85rem !important;}
        .overview-box {padding: 1rem; font-size: 0.95rem !important;}
        .overview-box h3 {font-size: 1.1rem !important;}
        .overview-box p {font-size: 0.95rem !important;}
        /* Stack rows vertically on very small screens */
        .gradio-row {flex-direction: column !important;}
        iframe[data-testid="embed-iframe"] {height: 250px !important;}
    }
"""

with gr.Blocks(title="What was 2024 about chart", theme=theme, css=CUSTOM_CSS) as demo:

    # Hero section with optional image
    with gr.Column(elem_classes=["hero"]):
        gr.Image(value=str(HEADER), show_label=False, height=300)

        gr.Markdown("# What Was 2024 About")
        gr.Markdown("_Results of your's favourite yearly music chart_")

        # Spotify Playlist Embed (centered)
        gr.HTML("""
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
        """)
        gr.Markdown(
            (
                "Note: Some songs (BABYS IN A THUNDERCLOUD by Godspeed You! Black Emperor, Veneficium by Xiu Xiu) were removed from "
                "Spotify by artists protesting Spotify's policies about their investment in drones/military investments. "
                "Also F*ck ICE just for the sake."
            ),
            elem_classes=["model-note"],
        )
        gr.Markdown(
            "<p style='font-size: 0.95rem; color: #ffffff !important; text-align: center; margin: 0.5rem 0 0.25rem;'>"
            "Please enter the same email prefix you used in the survey (before the @). This unlocks your personal insights."
            "</p>"
        )
        with gr.Row():
            email_input = gr.Textbox(
                label="Your email prefix",
                placeholder="e.g., macdemarco (without @gmail.com)",
                show_label=True
            )
            refresh_btn = gr.Button("Refresh Data 🔄", variant="primary")

    # Overview section (compact summary, no charts)
    with gr.Column(elem_classes=["overview-box"]):
        overview = gr.Markdown("")

    # Podium visualization
    gr.Markdown("## The Podium")
    gr.Markdown("_The champions. Song winners of last years. The chosen ones. The songs that made you fill '10' without hesitation (or maybe they tied at 7.29, who knows)._")
    podium_plot = gr.Plot()

    # Top 10 spotlight
    gr.Markdown("## Top 10 Spotlight")
    gr.Markdown("_Because everyone loves a top 10 list. No matter how many songs were in the final playlist, everyone loves top 10s._")
    top10_plot = gr.Plot()

    # Distribution charts side by side
    gr.Markdown("## Score Distributions")
    gr.Markdown("_Ever wondered if everyone's just vibing around 7s or if there are actual opinions happening? And what about your voting patterns? These histograms know._")
    with gr.Row():
        with gr.Column(scale=1):
            avg_dist_plot = gr.Plot()
        with gr.Column(scale=1):
            all_votes_plot = gr.Plot()

    # Full rankings
    gr.Markdown("## Complete Rankings")
    gr.Markdown("_All the songs. Every single one. Ranked from 'meh' to 'oh my, life changing song I am hearing'. Switch views to see where you agree or disagree._")
    with gr.Row():
        ranking_view = gr.Radio(
            label="View",
            choices=[
                "Final score + your score (overlay)",
                "Only final score",
                "Only your scores",
            ],
            value="Final score + your score (overlay)",
        )
    main_plot = gr.Plot()

    # All songs table and user comparison
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Overall Rankings")
            all_songs_table = gr.Dataframe(
                headers=["Rank", "Song", "Average Score"],
                interactive=False,
                wrap=True
            )
        with gr.Column(scale=1):
            gr.Markdown("### Your Votes vs Average")
            user_comparison = gr.Dataframe(
                headers=["Rank", "Song", "Average Score", "Your Score", "Difference"],
                interactive=False,
                wrap=True
            )

    # New user-specific visualizations (only shown when user email is provided)
    gr.Markdown("## Your Personal Music Analysis")
    warning_personal = gr.Markdown("<p style='color: #9333ea; font-size: 16px; font-weight: 600; margin-bottom: 10px;'>⚠️ To see your personalized insights, enter your email address above.</p>")
    gr.Markdown("This is where your music taste is analyzed (if you filled this year's survey). Enter your email above to unlock personalized insight.")

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
    warning_rating = gr.Markdown("<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>")
    gr.Markdown("_Are you a harsh critic handing out 3s like candy, or a generous soul showering 9s? This chart exposes your rating philosophy_")
    rating_pattern_plot = gr.Plot()

    gr.Markdown("## Community Insights")
    gr.Markdown("_Dive into the collective consciousness. See patterns, chaos, and who's secretly rating everything a 5._")

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
    gr.Markdown("_Explore music taste similarities (anonymized). Currently far from being useful, will come handy with more voters (please vote next years!)._")
    taste_map_plot = gr.Plot()

    gr.Markdown("## Your Music Taste Recommendations")
    warning_recommendations = gr.Markdown("<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above.</p>")
    gr.Markdown("_Generative AI (LLM) analyzes your favorites and suggests artists/genres to explore in 2025 - sometimes maybe good, sometimes maybe shit hallucination._")
    recommendations_box = gr.Markdown("")

    def refresh_with_email(email_prefix: str, ranking_view_choice: str):
        """Fetch the full dashboard for a given user and ranking view.

        Returns a long tuple of output values in the exact order defined by
        `all_outputs` below. Keeping the order stable is critical for Gradio wiring.
        """
        # Map radio string to simple key
        mapping = {
            "Final score + your score (overlay)": "overlay",
            "Only final score": "average",
            "Only your scores": "user",
        }
        view_key = mapping.get(ranking_view_choice, "overlay")
        results = create_dashboard(email_prefix, ranking_view=view_key)

        # Hide warnings if email is provided and has data
        has_data = email_prefix and email_prefix.strip() != ""
        warning_text = "" if has_data else "<p style='color: #9333ea; font-size: 16px; font-weight: 600;'>⚠️ To see your personalized insights, enter your email address above</p>"

        return (*results, warning_text, warning_text, warning_text)

    def refresh_main_chart_only(email_prefix: str, ranking_view_choice: str):
        """Refresh only the main chart when ranking view changes.

        This avoids recomputing and re-rendering all other blocks while the
        user toggles the main view radio.
        """
        mapping = {
            "Final score + your score (overlay)": "overlay",
            "Only final score": "average",
            "Only your scores": "user",
        }
        view_key = mapping.get(ranking_view_choice, "overlay")
        # Get full dashboard but only return main_plot (6th output)
        all_results = create_dashboard(email_prefix, ranking_view=view_key)
        return all_results[5]  # main_plot is the 6th item (index 5)

    # Wire up refresh with email
    all_outputs = [
        overview, podium_plot, top10_plot, avg_dist_plot, all_votes_plot, main_plot,
        all_songs_table, user_comparison,
        disagreements_plot, user_vs_top10_plot, heatmap_plot, controversy_plot, agreeable_plot,
        rating_pattern_plot,
        taste_map_plot,
        recommendations_box,
        warning_personal,
        warning_rating,
        warning_recommendations,
    ]

    refresh_btn.click(
        refresh_with_email,
        inputs=[email_input, ranking_view],
        outputs=all_outputs,
    )

    # Auto-refresh only main chart when ranking view changes
    ranking_view.change(
        refresh_main_chart_only,
        inputs=[email_input, ranking_view],
        outputs=main_plot,
    )

    # Email input triggers refresh too
    email_input.submit(
        refresh_with_email,
        inputs=[email_input, ranking_view],
        outputs=all_outputs,
    )

    # Initial load with empty email
    demo.load(
        lambda: (
            *create_dashboard("", ranking_view="overlay"),
            WARNING_HTML, WARNING_HTML, WARNING_HTML
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

    def submit_feedback(email_prefix: str, songs: str, ideas: str) -> str:
        """Handle feedback submission and return a user-facing status message.

        Behavior:
        - Always writes a text log file (best-effort) for persistence
        - Prefers WEBHOOK_URL for deployments; falls back to SMTP if configured locally
        - No secrets are stored; all creds are read from env
        """
        if not songs.strip() and not ideas.strip():
            return "⚠️ Please fill in at least one field before submitting!"

        try:
            import os
            import smtplib
            from datetime import datetime
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            import requests

            # Email configuration - get from environment variables
            sender_email = os.environ.get("SMTP_EMAIL", "")
            sender_password = os.environ.get("SMTP_PASSWORD", "")
            webhook_url = os.environ.get("WEBHOOK_URL", "")  # For Hugging Face deployment
            receiver_email = "maravasku@gmail.com"

            body = "New feedback received!\n\n"
            body += f"Email Prefix: {email_prefix.strip() if email_prefix and email_prefix.strip() else '(none)'}\n\n"

            if songs.strip():
                body += "=" * 50 + "\n"
                body += "🎵 SONG SUGGESTIONS FOR 2025:\n"
                body += "=" * 50 + "\n"
                body += songs.strip() + "\n\n"

            if ideas.strip():
                body += "=" * 50 + "\n"
                body += "💡 IMPROVEMENT IDEAS:\n"
                body += "=" * 50 + "\n"
                body += ideas.strip() + "\n\n"

            # Always save to file as backup
            try:
                with open('feedback_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Email Prefix: {email_prefix.strip() if email_prefix and email_prefix.strip() else '(none)'}\n")
                    f.write(f"{'='*60}\n")
                    f.write(body)
                file_saved = True
            except Exception:
                file_saved = False

            email_sent = False
            email_method = None
            error_msg = None

            # Try webhook first (works in Hugging Face Spaces)
            if webhook_url:
                try:
                    subject = f"Music Chart Feedback - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    if email_prefix and email_prefix.strip():
                        subject += f" | from: {email_prefix.strip()}"
                    
                    # Webhook payload: keep it minimal and structured (no duplicate fields)
                    payload = {
                        "to": receiver_email,
                        "subject": subject,
                        "body": body,
                        # Extra structured fields for downstream mappers (optional)
                        "email_prefix": email_prefix or "",
                        "songs_raw": songs.strip() if songs and songs.strip() else "",
                        "ideas_raw": ideas.strip() if ideas and ideas.strip() else "",
                    }
                    
                    # Try both JSON and form data formats
                    response = requests.post(webhook_url, json=payload, timeout=10)
                    if response.status_code == 200 or response.status_code == 201:
                        email_sent = True
                        email_method = "webhook"
                    else:
                        # Try form data if JSON failed
                        response = requests.post(webhook_url, data=payload, timeout=10)
                        if response.status_code == 200 or response.status_code == 201:
                            email_sent = True
                            email_method = "webhook"
                        else:
                            error_msg = f"Webhook returned status {response.status_code}"
                except Exception as e:
                    error_msg = f"Webhook error: {str(e)}"

            # Try SMTP if webhook didn't work (for local testing)
            if not email_sent and sender_email and sender_password:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    subject_suffix = f" | from: {email_prefix.strip()}" if email_prefix and email_prefix.strip() else ""
                    msg['Subject'] = f"Music Chart Feedback - {datetime.now().strftime('%Y-%m-%d %H:%M')}{subject_suffix}"
                    msg.attach(MIMEText(body, 'plain'))
                    
                    with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.send_message(msg)
                    email_sent = True
                    email_method = "SMTP"
                except Exception as e:
                    if not error_msg:
                        error_msg = f"SMTP error: {str(e)}"

            # Build response message
            if email_sent:
                message = f"✅ **Thank you!** Your feedback has been sent via {email_method}.\n\n"
            else:
                message = "✅ **Thank you!** Your feedback has been saved.\n\n"
                if error_msg:
                    message += f"ℹ️ {error_msg}\n\n"
                elif not webhook_url and not (sender_email and sender_password):
                    message += "ℹ️ Email notification unavailable (configure WEBHOOK_URL for Hugging Face or SMTP for local).\n\n"

            if songs.strip():
                message += f"**Songs suggested:** {len(songs.strip().splitlines())} lines\n"
            if ideas.strip():
                message += f"**Ideas shared:** {len(ideas.strip().splitlines())} lines\n"
            
            if not file_saved:
                message += "\n⚠️ Warning: Could not save to feedback log file."

            return message

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return f"❌ Error saving feedback: {str(e)}\n\nDetails:\n{error_trace}"

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
    # Launch a local server. Set share=True for a public link (useful for quick demos).
    demo.launch(share=False)