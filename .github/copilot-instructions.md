# AI Agent Instructions: What Was Year About

## Project Overview
A **Gradio web app** deployed on Hugging Face Spaces for visualizing yearly music survey results. Users vote on songs via Google Forms; responses are stored in Google Sheets and analyzed with Plotly visualizations, clustering (sklearn), and LLM-powered personalized insights via Groq API.

**Tech Stack:** Python 3.11, Gradio 5.49.1, Plotly (visuals), gspread (Google Sheets), Groq (LLM), scikit-learn (clustering), pandas/numpy (data)

## Architecture & Data Flow

### Multi-Year Support Pattern
The app supports **multiple years (2019, 2023, 2024)** with different data formats:
- **2024**: Modern format with voter-row matrix (Timestamp, Email, then one column per song)
- **2019/2023**: Legacy formats that get normalized via `_standardize_legacy_votes()` in `src/data_utils.py`
- Data fetching: `fetch_data(year)` in `src/load_data.py` handles all years
- Year selector in UI controlled via `year_selector` dropdown in `src/app_gradio.py`

### Core Data Pipeline
```
Google Sheets → gspread → DataFrame → compute_scores() → avg_scores + rankings
                                    ↓
                          user email filtering → comparison DataFrame → LLM insights
```

1. **Data Loading** (`src/load_data.py`): `fetch_data(year)` authenticates via service account credentials (env var `GOOGLE_SHEETS_CREDENTIALS` or `credentials.json` file) and loads year-specific sheets
2. **Score Computation** (`src/data_utils.py`): `compute_scores()` calculates average scores with **tied ranking** (competition rank: 1,1,3,4...) using `rank(method="min")`
3. **User Comparison** (`src/data_utils.py`): `compare_user_votes(email_prefix, year)` filters user votes by email prefix and computes difference vs averages
4. **Visualization** (`src/visuals.py`): All chart functions (`make_*_chart()`) return `plotly.graph_objects.Figure` instances
5. **Dashboard Generation** (`src/dashboard.py`): `create_dashboard(user_email_prefix, ranking_view, year)` orchestrates data + charts with LRU caching

### LLM Integration (Groq API)
- **Enable via env**: `GROQ_API_KEY` must be set (`src/llm_implementation.py`)
- **Three models for different tasks** (overrideable via env):
  - `MODEL_BLURB`: Short summaries (default: `llama-3.1-8b-instant`)
  - `MODEL_ANALYSIS`: User voting patterns (default: `openai/gpt-oss-120b`)
  - `MODEL_JSON`: Structured recommendations (default: `moonshotai/kimi-k2-instruct`)
- **Key functions**:
  - `get_user_voting_insight(comparison_df)`: Personalized voting pattern analysis (~250-300 words, conversational, no emojis/hero language)
  - `generate_recommendations(comparison, n=5)`: JSON-structured artist/genre recommendations based on top/bottom songs

## Critical Development Workflows

### Running the App
```bash
# Local development (loads .env file)
cd src && python app_gradio.py

# Hugging Face Spaces deployment
# Set repository secrets: GOOGLE_SHEETS_CREDENTIALS, GROQ_API_KEY, WEBHOOK_URL
# Entry point: src/app_gradio.py (defined in README.md frontmatter)
```

### Testing
```bash
# Run tests with pytest
python -m pytest src/test_recommendations.py -v

# Lint/format with ruff
ruff check src/
ruff format src/
```

### Dependency Management
Uses **uv** for lock file generation:
```bash
# Update requirements.txt from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt
```

### Environment Variables
**Required for production:**
- `GOOGLE_SHEETS_CREDENTIALS`: JSON content of service account (for Hugging Face Spaces)
- `GROQ_API_KEY`: Groq API key for LLM features

**Optional:**
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to credentials file (local fallback)
- `MODEL_BLURB`, `MODEL_ANALYSIS`, `MODEL_JSON`: Override default LLM models
- `WEBHOOK_URL`: Zapier webhook for feedback email notifications (Hugging Face)
- `SMTP_EMAIL`, `SMTP_PASSWORD`: SMTP fallback for local feedback testing

## Project-Specific Conventions

### Google Sheets Credential Handling
Three-tier fallback system in `src/load_data.py`:
1. `GOOGLE_SHEETS_CREDENTIALS` env var (JSON string) - preferred for Hugging Face Spaces
2. `GOOGLE_APPLICATION_CREDENTIALS` env var (file path)
3. `credentials.json` in project root (local development)

**Critical:** Always use `os.path.join(BASE_DIR, "credentials.json")` for root paths, never relative paths

### Tied Ranking Implementation
Use **competition ranking** (`rank(method="min")`) for ties:
```python
# Example: scores [9.5, 9.5, 8.0] → ranks [1, 1, 3]
avg_scores["Rank"] = avg_scores["Average Score"].rank(method="min", ascending=False).astype(int)
```
Display all tied songs together in podium (see `src/dashboard.py`)

### Data Caching Pattern
Use `@lru_cache(maxsize=10)` for expensive operations accepting multiple years/users:
```python
@lru_cache(maxsize=10)
def get_data_cached(user_email_prefix: str = "", year: int = 2024):
    # Cache key includes both params for year + user combinations
```

### Visualization Standards (Plotly)
All chart functions follow pattern:
```python
def make_*_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()  # Always return empty figure, never None
    # ... chart code
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='#fff',
        # Inter font family, centered titles
    )
    return fig
```

### Custom CSS Classes (Gradio)
Key CSS classes in `src/app_gradio.py`:
- `.hero`: Purple gradient header with centered content
- `.overview-box`: Light panel for winner/top-3 display (forces dark text on light bg)
- `.model-note`: Small gray text for LLM model attribution
- Mobile-responsive with breakpoints at `768px` and `480px`

### Email Prefix Filtering
User identification by **email prefix** (before `@`):
```python
def get_user_votes(df: pd.DataFrame, email_prefix: str):
    # Case-insensitive matching
    user_row = df[df['Email address'].str.lower().str.startswith(email_prefix.lower())]
```

### Feedback System
Dual submission in `src/app_gradio.py`:
1. **Primary**: POST to `WEBHOOK_URL` (Zapier → email, works in Hugging Face)
2. **Fallback**: SMTP via Gmail (local dev only)
3. **Backup**: Always append to `feedback_log.txt` for reliability

## Integration Points

### Google Sheets Structure
Expected columns (2024 format):
1. `Timestamp` (datetime)
2. `Email address` (voter identification)
3-N. Song columns in format `"Song Title - Artist"` with numeric ratings (1-10)

Legacy formats (2019/2023) get normalized via column detection in `_standardize_legacy_votes()`

### Groq API Interaction
- All LLM calls go through internal `call_groq()` function (see `src/llm_implementation.py`)
- JSON parsing robustness: handles markdown-wrapped JSON (`json```...```) from LLMs
- Fallback handling: Returns empty/default responses on API failure, never crashes UI

### Hugging Face Spaces Deployment
- **Runtime**: Python 3.11 (`runtime.txt`)
- **Metadata**: Frontmatter in `README.md` defines `app_file: src/app_gradio.py`
- **Secrets**: Set in Space settings, accessed via `os.environ.get()`

## Common Pitfalls

1. **Rankings with ties**: Always use `rank(method="min")` and display all tied songs
2. **Empty DataFrames**: Check `df.empty` before operations; return empty figures from chart functions
3. **Credential paths**: Use `BASE_DIR` constant, never `os.path.dirname(__file__)` directly in `src/load_data.py`
4. **Year normalization**: Handle 2019/2023 legacy formats differently from 2024 in `src/data_utils.py`
5. **LLM prompt constraints**: User analysis must be 250-300 words, no emojis, no hero language (see `src/llm_implementation.py`)
6. **Mobile CSS**: Test responsive breakpoints when modifying layout

## Key Files Reference

- `src/app_gradio.py`: Gradio UI entry point, event handlers, custom CSS
- `src/dashboard.py`: Main orchestration function `create_dashboard()`
- `src/data_utils.py`: Score computation, user filtering, clustering, caching
- `src/load_data.py`: Google Sheets authentication and data fetching
- `src/llm_implementation.py`: Groq API integration for insights/recommendations
- `src/visuals.py`: All Plotly chart generation functions
- `pyproject.toml`: Dependencies and ruff config (line-length: 120, target: py311)
