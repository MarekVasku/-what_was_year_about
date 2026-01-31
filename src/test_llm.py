import os
import sys

import pandas as pd

from llm_implementation import analyze_user_votes

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.append(src_path)


# Create a test comparison DataFrame with real song data
test_data = {
    "Song": ["Black Lipstick", "Starburster", "Nothing Matters"],
    "Your Score": [9.0, 7.0, 8.5],
    "Average Score": [6.5, 8.0, 7.5],
    "Difference": [2.5, -1.0, 1.0],
    "Rank": [1, 2, 3],
}
test_df = pd.DataFrame(test_data)

# Generate and print the analysis
print("\n=== Full LLM Response ===")
print("Input DataFrame:")
print(test_df)
print("\nGenerated Analysis:")
result = analyze_user_votes(test_df)
print(result)
print("\n=== End of Response ===\n")
