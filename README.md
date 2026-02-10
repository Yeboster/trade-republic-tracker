# Trade Republic Tracker

A Python-based tool to track Trade Republic finances, with a specific focus on **Card Transactions** (spending).

## Project Status

- **Iteration 1 & 2 (Auth & WebSocket):** Implemented in `src/tracker/client.py`. Uses `httpx` for REST Auth and `websockets` for real-time data.
- **Iteration 3 (Transaction History):** Implemented in `src/tracker/timeline.py`. Fetches full history via WebSocket pagination.
- **Iteration 4 (Data Parsing):** **Refined (2026-02-10).**
  - Validated field mapping against Reference Go implementation.
  - Confirmed mappings: `title` -> Merchant, `eventType` -> Transaction Type.
  - Fixed timestamp parsing for ISO formats (e.g., `2024-05-27T13:51:55.167+0000`).
  - Improved CSV export columns (`merchant`, `type`, `status`).
- **Iteration 5 (Analysis):** Implemented in `src/tracker/analysis.py`. Provides spending summary, monthly breakdown, and top merchants.

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run
export TR_PHONE="+4912345678"
export TR_PIN="1234"
python3 -m src.tracker.cli --output my_transactions.csv
```

## Structure

- `src/tracker/client.py`: Core API client (Auth + WebSocket).
- `src/tracker/timeline.py`: Timeline management and processing.
- `src/tracker/analysis.py`: Logic for spending reports and profit/loss calculation.
- `src/tracker/cli.py`: Command-line interface.
