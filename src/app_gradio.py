import gradio as gr
from gradio import themes
from dashboard import create_dashboard
from data_utils import refresh_data


# ---------- Gradio UI (UI-only, imports functionality from modules) ----------
theme = themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    neutral_hue="slate",
    font=themes.GoogleFont("Inter"),
).set(
    body_background_fill="*neutral_50",
    block_title_text_weight="600",
)

CUSTOM_CSS = """
    .gradio-container {max-width: 1400px !important;}
    .hero {text-align: center; padding: 2rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           border-radius: 12px; margin-bottom: 2rem; color: white;}
    .hero h1 {color: white !important; font-size: 2.5rem; margin-bottom: 0.5rem;}
    .hero p {font-size: 1.1rem; opacity: 0.9;}
    .overview-box {background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 2rem;
                  color: #374151 !important; line-height: 1.6 !important; font-size: 1.1rem !important;}
    .overview-box h1, .overview-box h2, .overview-box h3 {color: #1f2937 !important;}
    .overview-box h3 {font-size: 1.6rem !important; margin-top: 1.5rem !important; margin-bottom: 0.75rem !important;
                     font-weight: 600 !important; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem;}
    .overview-box p {font-size: 1.1rem !important; color: #374151 !important; margin-bottom: 1rem !important;}
    .stats-line {font-size: 1rem !important; color: #6b7280 !important; margin: 0.5rem 0 !important;}
"""

with gr.Blocks(title="2024 Best Alternative Songs", theme=theme, css=CUSTOM_CSS) as demo:
    
    # Hero section with optional image
    with gr.Column(elem_classes=["hero"]):
        gr.Image("/Users/macbok/Documents/Projects/-what_was_year_about/static/header.png", show_label=False, height=300)
        
        gr.Markdown("# What Was 2024 About")
        gr.Markdown("_Some people's definitive ranking of the best alternative songs_")
        
        # Spotify Playlist Embed
        gr.HTML("""
            <iframe data-testid="embed-iframe" style="border-radius:12px; margin: 1rem auto; display: block;" 
                    src="https://open.spotify.com/embed/playlist/5LplruxClPSYiAUjANLodn?utm_source=generator" 
                    width="100%" 
                    height="352" 
                    frameBorder="0" 
                    allowfullscreen="" 
                    allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
                    loading="lazy">
            </iframe>
        """)
        
        with gr.Row():
            email_input = gr.Textbox(
                label="Your Email Prefix",
                placeholder="e.g., maravasku (without @gmail.com)",
                show_label=True
            )
            refresh_btn = gr.Button("Refresh Data 🔄", variant="primary")
    
    # Overview section (compact summary, no charts)
    with gr.Column(elem_classes=["overview-box"]):
        overview = gr.Markdown("")
    
    # Podium visualization
    gr.Markdown("## The Podium")
    podium_plot = gr.Plot()
    
    # Top 10 spotlight
    gr.Markdown("## Top 10 Spotlight")
    top10_plot = gr.Plot()
    
    # Distribution charts side by side
    gr.Markdown("## Score Distributions")
    with gr.Row():
        with gr.Column(scale=1):
            avg_dist_plot = gr.Plot()
        with gr.Column(scale=1):
            all_votes_plot = gr.Plot()
    
    # Full rankings
    gr.Markdown("## Complete Rankings")
    main_plot = gr.Plot()
    
    # All songs table and user comparison
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Overall Rankings")
            all_songs_table = gr.Dataframe(
                headers=["Rank", "Song", "Average Score"],
                interactive=False,
                wrap=True
            )
        with gr.Column(scale=1):
            gr.Markdown("### 🎯 Your Votes vs Average")
            user_comparison = gr.Dataframe(
                headers=["Rank", "Song", "Average Score", "Your Score", "Difference"],
                interactive=False,
                wrap=True
            )
    
    # New user-specific visualizations (only shown when user email is provided)
    gr.Markdown("## 🎭 Your Personal Music Analysis")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Biggest Disagreements")
            disagreements_plot = gr.Plot()
        with gr.Column(scale=1):
            gr.Markdown("### Your Top 10 vs Community")
            user_vs_top10_plot = gr.Plot()
    
    gr.Markdown("### Your Rating Pattern")
    rating_pattern_plot = gr.Plot()
    
    gr.Markdown("## 📊 Community Insights")
    
    gr.Markdown("### All Votes Heatmap")
    gr.Markdown("_Voters are anonymized except you_")
    heatmap_plot = gr.Plot()
    
    gr.Markdown("### Most Polarizing Songs (Top 10)")
    controversy_plot = gr.Plot()
    
    gr.Markdown("### Most Agreeable Songs (Top 10)")
    agreeable_plot = gr.Plot()
    
    gr.Markdown("## 🧬 Clustering Analysis")
    
    gr.Markdown("### 2D Taste Map")
    gr.Markdown("_Explore music taste similarities (anonymized)_")
    taste_map_plot = gr.Plot()
    
    def refresh_with_email(email_prefix):
        """Wrapper to pass email to refresh_data."""
        return create_dashboard(email_prefix)
    
    # Wire up refresh with email
    all_outputs = [
        overview, podium_plot, top10_plot, avg_dist_plot, all_votes_plot, main_plot, 
        all_songs_table, user_comparison,
        disagreements_plot, user_vs_top10_plot, heatmap_plot, controversy_plot, agreeable_plot,
        rating_pattern_plot,
        taste_map_plot
    ]
    
    refresh_btn.click(
        refresh_with_email,
        inputs=[email_input],
        outputs=all_outputs,
    )
    
    # Email input triggers refresh too
    email_input.submit(
        refresh_with_email,
        inputs=[email_input],
        outputs=all_outputs,
    )
    
    # Initial load with empty email
    demo.load(
        lambda: create_dashboard(""),
        inputs=None,
        outputs=all_outputs,
    )


if __name__ == "__main__":

    demo.launch(share=False)  # Set share=True for public link
