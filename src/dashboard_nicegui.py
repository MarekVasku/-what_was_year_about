"""NiceGUI experimental dashboard.

This module is intentionally small: it demonstrates how the same
data + visuals can be rendered with NiceGUI for experimentation.

Run directly with: python src/dashboard_nicegui.py
"""
from nicegui import ui
from data_utils import get_data_cached
from visuals import (
    make_podium_chart,
    make_top_10_spotlight,
    make_main_chart,
    make_distribution_chart,
    make_all_votes_distribution,
)


def build_nicegui_dashboard() -> None:
    """Build a read-only NiceGUI page showing the dashboard."""
    df_raw, avg_scores, total_votes, avg_of_avgs, total_songs, error, _comparison = get_data_cached()

    ui.markdown('# What Was 2024 About')
    ui.markdown("_Your group's definitive ranking of the best alternative songs_")

    def on_refresh() -> None:
        # Clear the cached data and notify the user to reload the page.
        get_data_cached.cache_clear()
        ui.notify('Cache cleared — reload the page to see updated data', color='green')

    ui.button('Refresh Data', on_click=on_refresh)

    if error:
        ui.markdown(f"""### ⚠️ Error Loading Data
```
{error}
```""")
        return

    if avg_scores.empty:
        ui.markdown('### 📊 No Data Yet\nClick Refresh Data to load voting results.')
        return

    # Overview
    top1 = avg_scores[avg_scores['Rank'] == 1]
    top2 = avg_scores[avg_scores['Rank'] == 2]
    top3 = avg_scores[avg_scores['Rank'] == 3]

    if not top1.empty:
        winners = ' | '.join([f"{row['Song']}" for _, row in top1.iterrows()])
        winner_display = f"{winners} — **{top1.iloc[0]['Average Score']:.2f}**"
    else:
        winner_display = '—'

    top3_lines = [
        '🥇 ' + ' • '.join([f"{row['Song']} ({row['Average Score']:.2f})" for _, row in top1.iterrows()]) if not top1.empty else '🥇 —',
        '🥈 ' + ' • '.join([f"{row['Song']} ({row['Average Score']:.2f})" for _, row in top2.iterrows()]) if not top2.empty else '🥈 —',
        '🥉 ' + ' • '.join([f"{row['Song']} ({row['Average Score']:.2f})" for _, row in top3.iterrows()]) if not top3.empty else '🥉 —',
    ]
    top3_text = '\n'.join(top3_lines)

    overview = f"**Winner:** {winner_display}\n\n**Stats:** {total_votes} votes  •  {total_songs} songs  •  Average: {avg_of_avgs:.2f}\n\n**Top 3:**\n{top3_text}"
    ui.markdown(overview)

    # Charts
    ui.markdown('## The Podium')
    ui.plotly(make_podium_chart(avg_scores))

    ui.markdown('## Top 10 Spotlight')
    ui.plotly(make_top_10_spotlight(avg_scores))

    ui.markdown('## Score Distributions')
    with ui.row():
        with ui.column():
            ui.plotly(make_distribution_chart(avg_scores))
        with ui.column():
            ui.plotly(make_all_votes_distribution(df_raw))

    ui.markdown('## Complete Rankings')
    ui.plotly(make_main_chart(avg_scores))

    ui.markdown('### All Songs Data Table')
    # Use a simple table representation
    records = avg_scores[['Rank', 'Song', 'Average Score']].round(2).to_dict('records')
    ui.table.from_pandas(avg_scores[['Rank', 'Song', 'Average Score']].round(2))


if __name__ == '__main__':
    build_nicegui_dashboard()
    ui.run(title='What Was 2024 About - NiceGUI', reload=False)