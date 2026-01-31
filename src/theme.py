"""
Gradio theme and CSS styling for the music survey app.
Centralized theme configuration and custom CSS.
"""

from gradio import themes

# Theme configuration
THEME = themes.Soft(
    primary_hue="blue",
    secondary_hue="indigo",
    neutral_hue="slate",
    font=themes.GoogleFont("Inter"),
).set(
    body_background_fill="*neutral_950",
    block_title_text_weight="600",
)

# Custom CSS styles
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
