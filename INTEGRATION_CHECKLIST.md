# Integration Checklist

Use this checklist to gradually integrate the refactored modules into the codebase.

## Phase 1: Setup & Configuration (Do First)

- [ ] Add `pydantic-settings` to `pyproject.toml`
  ```toml
  dependencies = [
      ...
      "pydantic-settings>=2.0",
      ...
  ]
  ```

- [ ] Update `src/pyproject.toml` lock file
  ```bash
  uv pip compile pyproject.toml -o requirements.txt
  ```

- [ ] Test new modules import correctly
  ```bash
  python -c "from config import SUPPORTED_YEARS; print(SUPPORTED_YEARS)"
  python -c "from settings import settings; print(settings.llm_enabled)"
  ```

---

## Phase 2: Update app_gradio.py (Highest Impact)

**Current:** 520 lines, 500+ in CSS
**After:** ~100 lines, CSS moved to `theme.py`

### Changes:
- [ ] Replace CSS import
  ```python
  # Remove: CUSTOM_CSS = """...""" (all 500+ lines)
  # Add: from theme import THEME, CUSTOM_CSS
  ```

- [ ] Replace theme setup
  ```python
  # Remove: theme = themes.Soft(...).set(...)
  # Add: from theme import THEME; ... theme=THEME
  ```

- [ ] Replace environment loading
  ```python
  # Remove: from dotenv import load_dotenv; load_dotenv()
  # Add: from settings import settings
  ```

- [ ] Update radio choices
  ```python
  # Remove: choices=["Final score + your score (overlay)", ...]
  # Add: from config import RANKING_VIEW_CHOICES; choices=RANKING_VIEW_CHOICES
  ```

- [ ] Replace feedback handler
  ```python
  # Remove: lines 370-516 (submit_feedback function)
  # Add: from feedback import FeedbackSubmitter
  ```

---

## Phase 3: Update load_data.py

**Current:** Duplicated auth logic
**After:** Single source from `credentials.py`

### Changes:
- [ ] Replace auth fallback logic
  ```python
  # Remove: 3-tier fallback try-catch blocks
  # Add: from credentials import authenticate; gc = authenticate()
  ```

- [ ] Replace hardcoded spreadsheet name
  ```python
  # Remove: SPREADSHEET_NAME = "What was 2024 about - responses"
  # Add: from config import SPREADSHEET_CONFIG; spreadsheet = gc.open(SPREADSHEET_CONFIG[year])
  ```

- [ ] Add error handling
  ```python
  from exceptions import CredentialsError, DataError
  try:
      gc = authenticate()
  except CredentialsError as e:
      raise DataError(f"Failed to load data: {str(e)}")
  ```

---

## Phase 4: Update llm_implementation.py

**Current:** Duplicated auth, scattered prompts, mixed concerns
**After:** Clean imports, template-based prompts

### Changes:
- [ ] Replace auth logic
  ```python
  # Remove: fetch_df() auth duplication
  # Add: from credentials import authenticate
  ```

- [ ] Replace hardcoded models
  ```python
  # Remove: GROQ_MODEL = os.environ.get(...)
  # Add: from settings import settings; model = settings.model_analysis
  ```

- [ ] Replace prompt building with templates
  ```python
  # Replace: prompt = f"Write a friendly...\n{biggest_over}..."
  # With: from prompt_templates import render_voting_analysis_prompt
  #       prompt = render_voting_analysis_prompt(biggest_over, biggest_under, ...)
  ```

- [ ] Add error handling
  ```python
  from exceptions import LLMError
  try:
      response = client.chat.completions.create(...)
  except Exception as e:
      raise LLMError(f"LLM failed: {str(e)}")
  ```

---

## Phase 5: Update dashboard.py (Complex)

**Current:** 16-item tuple returns, mixed concerns
**After:** Type-safe `DashboardData`, better cache control

### Changes:
- [ ] Replace all return statements with `DashboardData`
  ```python
  # Before:
  # return (overview, podium_plot, top10_plot, ...)
  
  # After:
  from models import DashboardData
  return DashboardData(
      overview=overview,
      podium_plot=podium_plot,
      top10_plot=top10_plot,
      ...
  )
  ```

- [ ] Update error returns
  ```python
  # Before: return (..., error_fig, ..., "")
  # After: return DashboardData(..., error_message="error text")
  ```

- [ ] Replace `@lru_cache` with `CachedDataLoader`
  ```python
  from cache import CachedDataLoader
  
  # Before: @lru_cache(maxsize=10)
  # After:
  data_cache = CachedDataLoader(ttl_seconds=3600, max_size=10)
  
  # In create_dashboard:
  cache_key = (user_email_prefix, year)
  df_raw, avg_scores, ... = data_cache.get(
      cache_key,
      lambda: get_data_uncached(user_email_prefix, year)
  )
  ```

- [ ] Update app_gradio.py to handle `DashboardData`
  ```python
  # Before: overview, podium_plot, ... = create_dashboard(...)
  # After:
  dashboard_data = create_dashboard(...)
  results = dashboard_data.to_tuple()  # For Gradio compatibility
  overview, podium_plot, ... = results
  ```

---

## Phase 6: Update data_utils.py

**Current:** Spread across functions, mixed concerns
**After:** Centralized, error-handled, cached

### Changes:
- [ ] Replace `@lru_cache` with `CachedDataLoader`
  ```python
  from cache import CachedDataLoader
  data_cache = CachedDataLoader(ttl_seconds=3600)
  ```

- [ ] Add error handling to all functions
  ```python
  from exceptions import DataError
  try:
      # ... computation
  except Exception as e:
      raise DataError(f"Score computation failed: {str(e)}")
  ```

- [ ] Use config values
  ```python
  from config import SONG_COLUMNS_START_INDEX, SONG_SCORE_MIN_THRESHOLD
  ```

---

## Phase 7: Test Integration

- [ ] Run existing tests
  ```bash
  python -m pytest src/test_recommendations.py -v
  ```

- [ ] Run new tests
  ```bash
  python -m pytest src/test_data_utils.py src/test_load_data.py src/test_dashboard.py -v
  ```

- [ ] Start local app
  ```bash
  cd src && python app_gradio.py
  ```

- [ ] Test manually:
  - [ ] App loads without errors
  - [ ] Dashboard displays data
  - [ ] User comparison works
  - [ ] LLM insights generate (if enabled)
  - [ ] Feedback submission works

---

## Phase 8: Code Cleanup

After all integrations:

- [ ] Remove old duplicated code from `load_data.py` and `llm_implementation.py`
- [ ] Remove inline CSS from `app_gradio.py`
- [ ] Update docstrings to reference new modules
- [ ] Run linter and formatter
  ```bash
  ruff check src/
  ruff format src/
  ```

---

## Validation Checklist

Before committing:

- [ ] All imports resolve (no `ImportError`)
- [ ] All tests pass
  ```bash
  python -m pytest src/ -v
  ```
- [ ] Code formatted with ruff
  ```bash
  ruff format src/
  ```
- [ ] Linting passes
  ```bash
  ruff check src/
  ```
- [ ] App runs locally
  ```bash
  cd src && python app_gradio.py
  ```
- [ ] No breaking changes to Gradio UI
- [ ] Backward compatible (uses `DashboardData.to_tuple()`)

---

## Troubleshooting

### Import Errors
```bash
# Check if all modules are in src/
ls -la src/*.py | grep -E "(config|settings|credentials|exceptions|theme|models|cache|feedback|prompt_templates)"
```

### Settings Not Loaded
```python
# Debug settings
from settings import settings
print(settings.dict())  # Show all loaded settings
```

### Cache Not Working
```python
# Check cache stats
from cache import CachedDataLoader
cache = CachedDataLoader()
print(cache.stats)
```

### Test Failures
```bash
# Run with verbose output
python -m pytest src/test_*.py -v -s

# Run specific test
python -m pytest src/test_data_utils.py::TestComputeScores::test_compute_scores_basic -v
```

---

## Timeline Estimate

- **Phase 1 (Setup):** 10 minutes
- **Phase 2 (app_gradio.py):** 30 minutes
- **Phase 3 (load_data.py):** 20 minutes
- **Phase 4 (llm_implementation.py):** 25 minutes
- **Phase 5 (dashboard.py):** 45 minutes (most complex)
- **Phase 6 (data_utils.py):** 20 minutes
- **Phase 7 (Testing):** 30 minutes
- **Phase 8 (Cleanup):** 15 minutes

**Total:** ~3.5 hours (can be split across multiple sessions)

---

## Questions?

Refer to `REFACTORING_SUMMARY.md` for detailed documentation on each module.
