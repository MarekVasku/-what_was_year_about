import os
import pandas as pd

SPREADSHEET_NAME = "What was 2024 about - responses"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

# Require an API key
GROQ_API_KEY = os.environ["GROQ_API_KEY"]  # will crash if missing
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

def fetch_df() -> pd.DataFrame:
    import gspread
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    sh = gc.open(SPREADSHEET_NAME).sheet1
    return pd.DataFrame(sh.get_all_records())

def get_top_song(df: pd.DataFrame, meta_cols: int = 2):
    # assumes first 2 columns are metadata (Timestamp, Email); ratings follow
    song_cols = list(df.columns[meta_cols:])
    ratings = df[song_cols].apply(pd.to_numeric, errors="coerce")
    means = ratings.mean(skipna=True).dropna()
    if means.empty:
        raise ValueError("No numeric ratings found in the sheet.")
    return means.idxmax(), float(means.max())

def make_prompt(song: str, avg: float) -> str:
    return f"Write one short sentence: The favourite song was {song} with an average rating of {avg:.2f}, then one more sentence about that musical taste jokingly"

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
    
    prompt = f"""Write a playfully sarcastic yet friendly music analysis directly addressing the voter (use 'you' and 'your'). Make it fun and personal, like a friend teasing another friend about their music taste. Around 200 words.

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
    
    return call_groq(prompt)

def call_groq(prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
        top_p=1,
        stop=None
    )
    return resp.choices[0].message.content.strip()

def get_user_voting_insight(comparison_df: pd.DataFrame) -> str:
    """Get an LLM-generated insight about how this user's votes compare to the group."""
    if comparison_df is None or comparison_df.empty:
        return ""
        
    try:
        analysis = analyze_user_votes(comparison_df)
        return analysis
    except Exception as e:
        return f"Could not generate insight: {str(e)}"

if __name__ == "__main__":
    df = fetch_df()
    song, avg = get_top_song(df, meta_cols=2)
    prompt = make_prompt(song, avg)
    text = call_groq(prompt)
    print(text, flush=True)
