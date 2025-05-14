import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
df = pd.read_csv("../../arbitrage_opportunities.csv")

# Sort by net profit percentage and select top 10 rows with desired columns
top_10_with_timestamp = df.sort_values(by="net_profit_percentage", ascending=False).head(10)[
    ["timestamp", "asset_pair", "buy_exchange", "sell_exchange", "net_profit_percentage"]
]

# Set up the figure and axis
fig, ax = plt.subplots(figsize=(12, 4))
ax.axis('tight')
ax.axis('off')

# Create a table
table = ax.table(cellText=top_10_with_timestamp.values,
                 colLabels=top_10_with_timestamp.columns,
                 cellLoc='center',
                 loc='center')

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.5)

# Save the table as an image
plt.savefig("top_10_highest_profit_table.png", bbox_inches='tight')
