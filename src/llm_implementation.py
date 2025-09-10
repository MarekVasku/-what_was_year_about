import os
import pandas as pd
import gspread
from groq import Groq

SPREADSHEET_NAME = "What was 2024 about - responses"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

# Require an API key
GROQ_API_KEY = os.environ["GROQ_API_KEY"]  # will crash if missing
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

def fetch_df() -> pd.DataFrame:
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

def call_groq(prompt: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=60,
    )
    return resp.choices[0].message.content.strip()

if __name__ == "__main__":
    df = fetch_df()
    song, avg = get_top_song(df, meta_cols=2)
    prompt = make_prompt(song, avg)
    text = call_groq(prompt)
    print(text, flush=True)
