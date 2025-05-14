
import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
df = pd.read_csv("../../arbitrage_opportunities.csv")

# Count the occurrences of each network used
network_counts = df["network_used"].value_counts()

# Calculate the percentage for top 10 only
top_10_networks_percent = (network_counts.head(10) / network_counts.sum()) * 100

# Plot bar chart with percentages using blue color
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(top_10_networks_percent.index, top_10_networks_percent.values, color='dodgerblue')

# Annotate bars with percentage values
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height:.1f}%', ha='center', va='bottom')

ax.set_ylabel("Percentage")
ax.set_title(f"Top 10 Most Frequently Used Networks (Total Unique Networks: {network_counts.count()})")
plt.xticks(rotation=45)

# Save as PNG
plt.tight_layout()
plt.savefig("top_10_networks_percentage_bar_blue.png")
