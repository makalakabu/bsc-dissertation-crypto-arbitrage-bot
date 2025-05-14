import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = "../../arbitrage_opportunities.csv"
df = pd.read_csv(file_path)

# Count the occurrences of each asset_pair
asset_pair_counts = df["asset_pair"].value_counts().head(10)

# Count how many unique asset pairs exist
unique_asset_pairs_count = df["asset_pair"].nunique()

# Create a horizontal bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(asset_pair_counts.index, asset_pair_counts.values, color="skyblue")
ax.set_xlabel("Frequency")
ax.set_title(f"Top 10 Most Frequently Evaluated Asset Pairs (Total Unique: {unique_asset_pairs_count})")
ax.invert_yaxis()  # Highest at the top

# Annotate bars with count values
for bar in bars:
    width = bar.get_width()
    ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center')

# Save the plot as PNG
plt.tight_layout()
plt.savefig("top_10_asset_pairs_bar_chart_with_total.png")
