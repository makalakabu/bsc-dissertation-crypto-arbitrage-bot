import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
file_path = "../../arbitrage_opportunities.csv"
df = pd.read_csv(file_path)

# Count the occurrences of each buy_exchange
buy_exchange_counts = df["buy_exchange"].value_counts()

# Define custom colors for exchanges
colors = []
for exchange in buy_exchange_counts.index:
    if exchange.lower() == "binance":
        colors.append("#F3BA2F")  # Binance yellow
    elif exchange.lower() == "okx":
        colors.append("#000000")  # OKX black
    else:
        colors.append("gray")  # Default color

# Plot pie chart with white percentage text and custom colors
fig, ax = plt.subplots()
wedges, texts, autotexts = ax.pie(
    buy_exchange_counts,
    labels=buy_exchange_counts.index,
    autopct='%1.1f%%',
    startangle=140,
    colors=colors
)

# Set percentage text color to white
for autotext in autotexts:
    autotext.set_color("white")

ax.axis('equal')
plt.title(f"Buy Exchange Distribution (Total: {buy_exchange_counts.sum()})")

# Save the chart as a PNG file
plt.savefig("buy_exchange_pie_chart_final.png")
