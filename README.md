# TradeLens Engine

TradeLens is a local Python-based trading journal, analytics engine, and risk-management compliance checker designed to parse messy broker reports and MT5 CSVs, standardize currencies, and enforce trading discipline rules.

## Project Structure
- `run.py`: Core execution script for data ingestion, rule evaluation, and reporting.
- `test_tradelens.py`: Automated test suite using `pytest`.
- `sample/`: Directory containing sample broker data, MT5 CSVs, and `rules.json`.
- `output/`: Generated reports (`trades.csv`, `summary.json`, `violations.csv`, `report.md`).

## Setup & Installation

1. Clone the repository and navigate into the project folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt