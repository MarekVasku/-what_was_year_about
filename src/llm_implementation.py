import pandas as pd

from config import DEFAULT_YEAR, SPREADSHEET_CONFIG
from credentials import authenticate
from prompt_templates import (
    render_recommendations_prompt,
    render_song_blurb_prompt,
    render_voting_analysis_prompt,
)
from settings import settings

# Require an API key
GROQ_API_KEY = settings.groq_api_key
LLM_ENABLED = settings.llm_enabled

# Default model fallbacks (can be overridden via env)
MODEL_BLURB = settings.model_blurb
MODEL_ANALYSIS = settings.model_analysis
MODEL_JSON = settings.model_json

# Legacy single-model env for backward compatibility
GROQ_MODEL = settings.groq_model or MODEL_BLURB

def fetch_df() -> pd.DataFrame:
    """Fetch Google Sheet into a DataFrame.

    Prefers credentials from the GOOGLE_SHEETS_CREDENTIALS env var (JSON string)
    for platforms like Hugging Face Spaces. Falls back to credentials.json file
    in the project root if the env var is not provided or parsing fails.
    """
    gc = authenticate()
    sh = gc.open(SPREADSHEET_CONFIG[DEFAULT_YEAR]).sheet1
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
    return render_song_blurb_prompt(song_name=song, avg_score=avg)

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

    # Create prompt for LLM using templates
    # Find biggest positive and negative differences
    biggest_over = (
        significant_diffs[significant_diffs['Difference'] > 0].iloc[0]
        if not significant_diffs[significant_diffs['Difference'] > 0].empty
        else None
    )
    biggest_under = (
        significant_diffs[significant_diffs['Difference'] < 0].iloc[0]
        if not significant_diffs[significant_diffs['Difference'] < 0].empty
        else None
    )

    biggest_over_data = None
    if biggest_over is not None:
        biggest_over_data = {
            "song": biggest_over["Song"],
            "score": float(biggest_over["Your Score"]),
            "avg_score": float(biggest_over["Average Score"]),
        }

    biggest_under_data = None
    if biggest_under is not None:
        biggest_under_data = {
            "song": biggest_under["Song"],
            "score": float(biggest_under["Your Score"]),
            "avg_score": float(biggest_under["Average Score"]),
        }

    disagreements = [
        (
            row["Song"],
            float(row["Your Score"]),
            float(row["Average Score"]),
            float(row["Difference"]),
        )
        for _, row in significant_diffs.iterrows()
    ]

    prompt = render_voting_analysis_prompt(
        biggest_over=biggest_over_data,
        biggest_under=biggest_under_data,
        top_user_songs=user_top["Song"].tolist(),
        top_community_songs=overall_top["Song"].tolist(),
        higher_count=int(higher_count),
        lower_count=int(lower_count),
        disagreements=disagreements,
    )

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

    # Sanitize song names to prevent JSON parsing issues with escape sequences
    def sanitize_song(song: str) -> str:
        """Remove problematic characters from song names."""
        return song.replace('\\', '/').replace('\n', ' ').replace('\r', ' ').strip()
    
    top5_clean = [sanitize_song(s) for s in top5]
    bottom5_clean = [sanitize_song(s) for s in bottom5]

    # Build prompt for artist/genre recommendations (more grounded, less hallucination)
    prompt = render_recommendations_prompt(top_songs=top5_clean, bottom_songs=bottom5_clean, n=n)

    try:
        # Structured JSON output model, lower temperature
        response = call_groq(prompt, MODEL_JSON, temperature=0.2, max_tokens=800)

        # Try to parse JSON from response
        import json
        import re

        # Extract JSON array if wrapped in markdown or other text
        # Try to find balanced brackets to handle complex content
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                recommendations = json.loads(json_str)
            except json.JSONDecodeError:
                # Try with re.escape to handle backslashes in content
                # Find first [ and last ] and extract everything between
                start_idx = response.find('[')
                end_idx = response.rfind(']')
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx + 1]
                    try:
                        recommendations = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        # If still failing, return empty with helpful error
                        return [{
                            'song': 'Unable to parse recommendations',
                            'artist': '',
                            'reason': f'JSON parsing error: {str(e)[:100]}'
                        }]
                else:
                    return [{
                        'song': 'Unable to analyze taste',
                        'artist': '',
                        'reason': 'Could not find JSON in AI response.'
                    }]

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
            'reason': f'An error occurred: {str(e)[:100]}'
        }]


if __name__ == "__main__":
    df = fetch_df()
    song, avg = get_top_song(df, meta_cols=2)
    prompt = make_prompt(song, avg)
    # Fast blurb model for short copy
    text = call_groq(prompt, MODEL_BLURB, temperature=0.5, max_tokens=80)
    print(text, flush=True)
