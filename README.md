# Trade Republic Tracker

A Python-based tool to track Trade Republic finances, with a specific focus on **Card Transactions** (spending).

## Project Status

- **Iteration 1 & 2 (Auth & WebSocket):** Implemented in `src/tracker/client.py`. Uses `httpx` for REST Auth and `websockets` for real-time data.
- **Iteration 3 (Transaction History):** Implemented in `src/tracker/timeline.py`. Fetches full history via WebSocket pagination.
- **Iteration 4 (Data Parsing):** **Completed (2026-02-10).**
  - Robust classification using `eventType` (e.g. `card_successful_transaction` vs `ORDER_EXECUTED`).
  - Fallback heuristics for older data.
  - CSV export now includes `event_type` for debugging.
  - Validated field mapping against Reference Go implementation.
- **Iteration 5 (Analysis):** **Completed (2026-02-10).**
  - Implemented `PortfolioAnalyzer` in `src/tracker/analysis.py`.
  - Provides Card Spending summary (Net Spent, Refunds, Top Merchants, Category breakdown).
  - Provides Investment summary (Net Invested, Top Assets).
  - Monthly breakdown of In/Out for both Cards and Investments.
- **Iteration 6 (Refinement):** **Completed (2026-02-10).**
  - Improved WebSocket stability (timeout handling, connection checks, graceful error recovery).
  - Updated to use `timelineDetailV2` for fetching transaction details, matching the official app's behavior.
  - Added robust response filtering to ignore echo/heartbeat messages.

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
