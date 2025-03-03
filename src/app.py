from nicegui import ui
from load_data import fetch_data
from dashboard import show_dashboard


# Load the voting data
df = fetch_data()

# Define the UI page
@ui.page("/")
def main_page():
    show_dashboard(df)

# Run the NiceGUI app
ui.run(title="What Was Year About - 2024 Music Votes", port=8080)
