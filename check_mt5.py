
import json
from src.mt5_processor import process_mt5_files

# Read exchange rate
with open("sample/rules.json", "r") as file:
    rules = json.load(file)

usd_inr = rules["usd_inr"]

# Process MT5 files
trades = process_mt5_files(
    "sample/data",
    usd_inr
)

# Display results
print("Total MT5 trades:", len(trades))
print("\nFirst 5 trades:")
print(trades.head().to_string(index=False))

print("\nDuplicate IDs:", trades["trade_id"].duplicated().sum())
print("\nAsset classes:")
print(trades["asset_class"].value_counts())
