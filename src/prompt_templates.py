"""
LLM prompt templates using Jinja2.
Centralizes prompt engineering and makes it maintainable.
"""

from jinja2 import Template

from config import LLM_ANALYSIS_MAX_WORDS, LLM_ANALYSIS_MIN_WORDS

# ============================================================================
# USER VOTING ANALYSIS PROMPT
# ============================================================================

VOTING_ANALYSIS_PROMPT = Template("""Write a friendly, conversational analysis that directly addresses the voter (use 'you' and 'your'). Keep it grounded and observational about preferences and results. Aim for {{ min_words }}–{{ max_words }} words.

Tone constraints (important):
- No hype or hero language. Avoid praise like "brave", "bold", "fearless", "iconic", or marathon-style metaphors.
- Do not judge the taste; treat it as preference, not achievement.
- Light, good‑natured teasing is fine, but keep it respectful and specific.
- Focus on what the votes show: over/under compared to the group, patterns, and concrete examples.

Formatting constraints:
- Do not use emojis or emoticons.
- Do not include headings or markdown titles; write plain paragraphs only.

Key points to hit with some gentle snark:
- {{ biggest_over_text }}
- {{ biggest_under_text }}
- Your top picks ({{ top_user_songs }}) vs what everyone else is raving about ({{ top_community_songs }})
- You rated {{ higher_count }} songs higher and {{ lower_count }} songs lower than the crowd - interesting pattern there!

Tone guide: Think "your music-obsessed friend who loves to playfully debate taste but ultimately celebrates your unique preferences". Mix gentle teasing with genuine appreciation for their bold choices. Throw in some music-nerd references if they fit.

Significant disagreements to mention:
{% for song, score, avg, diff in disagreements %}
- Rated '{{ song }}' {{ diff|abs|round(1) }} points {{ "higher" if diff > 0 else "lower" }} than the crowd (your {{ score|round(1) }} vs their {{ avg|round(1) }})
{% endfor %}"
""")


# ============================================================================
# ARTIST/GENRE RECOMMENDATIONS PROMPT
# ============================================================================

RECOMMENDATIONS_PROMPT = Template("""Based on the user's music taste (top songs and bottom songs), generate {{ n }} artist or genre recommendations for 2025.

Top songs they loved:
{% for song in top_songs %}
- {{ song }}
{% endfor %}

Songs they didn't rate as highly:
{% for song in bottom_songs %}
- {{ song }}
{% endfor %}

Generate recommendations as valid JSON array (no markdown wrapping):
[
  {
        "song": "Artist/Genre Name",
        "artist": "",
        "reason": "2-3 sentence explanation connecting to their taste"
  }
]

Focus on:
- Artists with similar vibes to their top songs
- Genres they clearly prefer based on their ratings
- Hidden gems they might discover
- Do NOT recommend mainstream artists they likely already know
- Be specific and thoughtful, not generic

Return only valid JSON, no additional text or markdown code blocks.
""")


# ============================================================================
# SONG BLURB PROMPT
# ============================================================================

SONG_BLURB_PROMPT = Template("""Write a short, witty blurb (2-3 sentences) about this year's music chart.

The favourite song was '{{ song_name }}' with an average rating of {{ avg_score|round(2) }}.

Then add one more sentence about that musical taste playfully.

Keep it light, fun, and under 50 words total.
""")


# ============================================================================
# TEMPLATE HELPERS
# ============================================================================


def render_voting_analysis_prompt(
    biggest_over: dict,
    biggest_under: dict,
    top_user_songs: list,
    top_community_songs: list,
    higher_count: int,
    lower_count: int,
    disagreements: list,
    min_words: int = LLM_ANALYSIS_MIN_WORDS,
    max_words: int = LLM_ANALYSIS_MAX_WORDS,
) -> str:
    """
    Render the voting analysis prompt with data.

    Args:
        biggest_over: Dict with 'song', 'score', 'avg_score' for most overrated song
        biggest_under: Dict with 'song', 'score', 'avg_score' for most underrated song
        top_user_songs: List of user's top 3 songs
        top_community_songs: List of community's top 3 songs
        higher_count: Number of songs rated higher than community
        lower_count: Number of songs rated lower than community
        disagreements: List of (song, user_score, avg_score, diff) tuples
        min_words: Minimum word count
        max_words: Maximum word count

    Returns:
        Rendered prompt string
    """
    biggest_over_text = ""
    if biggest_over:
        biggest_over_text = (
            f"You're absolutely swooning over '{biggest_over['song']}' with a "
            f"{biggest_over['score']:.1f} (while everyone else gave it a modest "
            f"{biggest_over['avg_score']:.1f})"
        )

    biggest_under_text = ""
    if biggest_under:
        biggest_under_text = (
            f"and giving '{biggest_under['song']}' a {biggest_under['score']:.1f} "
            f"(compared to the crowd's love at {biggest_under['avg_score']:.1f})"
        )

    return VOTING_ANALYSIS_PROMPT.render(
        min_words=min_words,
        max_words=max_words,
        biggest_over_text=biggest_over_text,
        biggest_under_text=biggest_under_text,
        top_user_songs=", ".join(top_user_songs),
        top_community_songs=", ".join(top_community_songs),
        higher_count=higher_count,
        lower_count=lower_count,
        disagreements=disagreements,
    )


def render_recommendations_prompt(
    top_songs: list,
    bottom_songs: list,
    n: int = 5,
) -> str:
    """
    Render the recommendations prompt.

    Args:
        top_songs: List of user's top songs
        bottom_songs: List of user's bottom songs

    Returns:
        Rendered prompt string
    """
    return RECOMMENDATIONS_PROMPT.render(
        top_songs=top_songs,
        bottom_songs=bottom_songs,
        n=n,
    )


def render_song_blurb_prompt(
    song_name: str,
    avg_score: float,
) -> str:
    """
    Render the song blurb prompt.

    Args:
        song_name: Name of the top song
        avg_score: Average score for the song

    Returns:
        Rendered prompt string
    """
    return SONG_BLURB_PROMPT.render(
        song_name=song_name,
        avg_score=avg_score,
    )
