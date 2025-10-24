import os

import pandas as pd

SPREADSHEET_NAME = "What was 2024 about - responses"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

# Require an API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_ENABLED = bool(GROQ_API_KEY)

# Default model fallbacks (can be overridden via env)
MODEL_BLURB = os.environ.get("MODEL_BLURB", "llama-3.1-8b-instant")
MODEL_ANALYSIS = os.environ.get("MODEL_ANALYSIS", "openai/gpt-oss-120b")
MODEL_JSON = os.environ.get("MODEL_JSON", "moonshotai/kimi-k2-instruct")

# Legacy single-model env for backward compatibility
GROQ_MODEL = os.environ.get("GROQ_MODEL", MODEL_BLURB)

def fetch_df() -> pd.DataFrame:
    """Fetch Google Sheet into a DataFrame.

    Prefers credentials from the GOOGLE_SHEETS_CREDENTIALS env var (JSON string)
    for platforms like Hugging Face Spaces. Falls back to credentials.json file
    in the project root if the env var is not provided or parsing fails.
    """
    import gspread
    import json

    gc = None
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            gc = gspread.service_account_from_dict(creds_dict)
        except Exception:
            # Fall back to file if env var is malformed
            gc = gspread.service_account(filename=CREDENTIALS_PATH)
    else:
        gc = gspread.service_account(filename=CREDENTIALS_PATH)

    sh = gc.open(SPREADSHEET_NAME).sheet1
    return pd.DataFrame(sh.get_all_records())

def get_top_song(df: pd.DataFrame, meta_cols: int = 2) -> tuple[str, float]:
    # assumes first 2 columns are metadata (Timestamp, Email); ratings follow
    song_cols = list(df.columns[meta_cols:])
    ratings = df[song_cols].apply(pd.to_numeric, errors="coerce")
    means = ratings.mean(skipna=True).dropna()
    if means.empty:
        raise ValueError("No numeric ratings found in the sheet.")
    top_song = str(means.idxmax())
    top_score = float(means.max())
    return top_song, top_score

def make_prompt(song: str, avg: float) -> str:
    return (
        f"Write one short sentence: The favourite song was {song} with an average rating of {avg:.2f}, "
        f"then one more sentence about that musical taste jokingly"
    )

def analyze_user_votes(comparison_df: pd.DataFrame) -> str:
    """Analyze how a user's votes differ from the average and generate a summary."""
    if comparison_df.empty:
        return ""

    # Sort by absolute difference to find most significant disagreements
    comparison_df = comparison_df.copy()
    comparison_df['Abs_Diff'] = abs(comparison_df['Difference'])
    significant_diffs = comparison_df.nlargest(3, 'Abs_Diff')

    # Find their top rated songs vs overall top rated
    user_top = comparison_df.nlargest(3, 'Your Score')
    overall_top = comparison_df.nlargest(3, 'Average Score')

    # Find general voting pattern
    avg_difference = comparison_df['Difference'].mean()
    higher_count = (comparison_df['Difference'] > 1).sum()
    lower_count = (comparison_df['Difference'] < -1).sum()

    # Create prompt for LLM
    # Find biggest positive and negative differences
    biggest_over = significant_diffs[significant_diffs['Difference'] > 0].iloc[0] if not significant_diffs[significant_diffs['Difference'] > 0].empty else None
    biggest_under = significant_diffs[significant_diffs['Difference'] < 0].iloc[0] if not significant_diffs[significant_diffs['Difference'] < 0].empty else None

    over_text = f"You're absolutely swooning over '{biggest_over['Song']}' with a {biggest_over['Your Score']:.1f} (while everyone else gave it a modest {biggest_over['Average Score']:.1f})" if biggest_over is not None else ""
    under_text = f"and giving '{biggest_under['Song']}' a {biggest_under['Your Score']:.1f} (compared to the crowd's love at {biggest_under['Average Score']:.1f})" if biggest_under is not None else ""

    prompt = f"""Write a friendly, conversational analysis that directly addresses the voter (use 'you' and 'your'). Keep it grounded and observational about preferences and results. Aim for 250–300 words.

Tone constraints (important):
- No hype or hero language. Avoid praise like "brave", "bold", "fearless", "iconic", or marathon-style metaphors.
- Do not judge the taste; treat it as preference, not achievement.
- Light, good‑natured teasing is fine, but keep it respectful and specific.
- Focus on what the votes show: over/under compared to the group, patterns, and concrete examples.

Formatting constraints:
- Do not use emojis or emoticons.
- Do not include headings or markdown titles; write plain paragraphs only.

Key points to hit with some gentle snark:
- {over_text}
- {under_text}
- Your top picks ({', '.join(user_top['Song'].tolist())}) vs what everyone else is raving about ({', '.join(overall_top['Song'].tolist())})
- You rated {higher_count} songs higher and {lower_count} songs lower than the crowd - interesting pattern there!

Tone guide: Think "your music-obsessed friend who loves to playfully debate taste but ultimately celebrates your unique preferences". Mix gentle teasing with genuine appreciation for their bold choices. Throw in some music-nerd references if they fit."""

    for _, row in significant_diffs.iterrows():
        diff = row['Difference']
        direction = 'higher' if diff > 0 else 'lower'
        prompt += f"\n- Rated '{row['Song']}' {abs(diff):.1f} points {direction} than the crowd"

    # Use the long-form analysis model as recommended
    # Request a longer output and auto-finish if the model cuts mid-sentence
    analysis = call_groq(prompt, MODEL_ANALYSIS, temperature=0.5, max_tokens=900)

    def is_complete(text: str) -> bool:
        t = text.strip()
        return len(t) > 0 and t[-1] in ".!?\u2026"  # ends with sentence punctuation

    if not is_complete(analysis):
        tail = call_groq(
            (
                "Continue and finish the above analysis cleanly in the same tone. "
                "Do not repeat prior lines; add 2–3 concluding sentences.\n\n"
                f"Previous text:\n{analysis}\n"
            ),
            MODEL_ANALYSIS,
            temperature=0.5,
            max_tokens=240,
        )
        analysis = (analysis.strip() + " " + tail.strip()).strip()
    return analysis

def call_groq(
        
    prompt: str,
    model: str | None = None,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    try:
        if not LLM_ENABLED:
            # LLM features disabled when no API key is configured; return empty
            # string so callers can decide how to render the absence of content.
            return ""
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        # Select model with sensible defaults based on env or provided override
        _model = model or GROQ_MODEL
        resp = client.chat.completions.create(
            model=_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7 if temperature is None else float(temperature),
            max_tokens=500 if max_tokens is None else int(max_tokens),
            top_p=1,
            stop=None
        )
        content = resp.choices[0].message.content
        return content.strip() if content else "No response generated"
    except Exception as e:
        return f"Error generating response: {str(e)}"

def get_user_voting_insight(comparison_df: pd.DataFrame) -> str:
    """Get an LLM-generated insight about how this user's votes compare to the group."""
    if comparison_df is None or comparison_df.empty:
        return ""

    try:
        analysis = analyze_user_votes(comparison_df)
        return analysis
    except Exception as e:
        return f"Could not generate insight: {str(e)}"


def generate_recommendations(top5: list[str], bottom5: list[str], n: int = 5) -> list[dict[str, str]]:
    """Generate artist/genre recommendations based on user's top 5 and bottom 5 songs.
    
    Args:
        top5: List of user's top 5 rated songs
        bottom5: List of user's bottom 5 rated songs  
        n: Number of recommendations to generate (default 5)
        
    Returns:
        List of dicts with keys: 'song' (used for artist/genre), 'artist' (empty), 'reason'
        Returns empty list on error
    """
    if not top5:
        return []

    # Build prompt for artist/genre recommendations (more grounded, less hallucination)
    prompt = f"""Based on someone's music taste, suggest {n} artists or music genres they should explore in 2025.

Their TOP 5 favorite songs from 2024:
{chr(10).join(f"- {song}" for song in top5)}

Their BOTTOM 5 least favorite songs from 2024:
{chr(10).join(f"- {song}" for song in bottom5)}

Analyze the QUALITIES in their top picks (mood, energy, production style, themes, etc.) and suggest artists or genres that match those qualities.

Respond ONLY with a valid JSON array. Each object must have exactly these fields:
- "song": the artist name OR genre/style (e.g., "Bicep" or "Melodic Techno")
- "artist": leave this as an empty string ""
- "reason": a brief (25-35 words) explanation connecting specific qualities from their top 5 to this recommendation

Example format:
[
  {{"song": "Fred again..", "artist": "", "reason": "Your top picks show a love for emotional electronic music with organic textures. Fred's live energy and melodic approach would resonate with your taste."}},
  {{"song": "Indie Folk with Electronic Elements", "artist": "", "reason": "The introspective lyrics and layered production in your favorites suggest you'd enjoy this genre blend."}}
]

Important:
- Focus on REAL artists or established genres/styles
- Base suggestions on specific qualities from their top 5 (mood, tempo, production, vocals, etc.)
- Avoid suggesting anything similar to their bottom 5
- Be specific in your reasoning - mention actual qualities you noticed
- Prioritize artists who are new in 2025 OR released a notable album/EP in 2025. If suggesting a genre, mention a 2025 wave or trend.
- When possible, reference 2025 releases succinctly (e.g., “new 2025 LP showcases …”).
- Return valid JSON only, no additional text"""

    try:
        # Structured JSON output model, lower temperature
        response = call_groq(prompt, MODEL_JSON, temperature=0.2, max_tokens=800)

        # Try to parse JSON from response
        import json
        import re

        # Extract JSON array if wrapped in markdown or other text
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            recommendations = json.loads(json_str)

            # Validate structure
            if isinstance(recommendations, list):
                valid_recs = []
                for rec in recommendations[:n]:  # Limit to n recommendations
                    if isinstance(rec, dict) and all(k in rec for k in ['song', 'artist', 'reason']):
                        valid_recs.append({
                            'song': str(rec['song']),
                            'artist': str(rec['artist']),
                            'reason': str(rec['reason'])
                        })
                return valid_recs

        # Fallback if JSON parsing fails
        return [{
            'song': 'Unable to analyze taste',
            'artist': '',
            'reason': 'Could not parse AI response. Please try refreshing.'
        }]

    except Exception as e:
        return [{
            'song': 'Error generating recommendations',
            'artist': '',
            'reason': f'An error occurred: {str(e)}'
        }]


if __name__ == "__main__":
    df = fetch_df()
    song, avg = get_top_song(df, meta_cols=2)
    prompt = make_prompt(song, avg)
    # Fast blurb model for short copy
    text = call_groq(prompt, MODEL_BLURB, temperature=0.5, max_tokens=80)
    print(text, flush=True)
