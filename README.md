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
  - **Spending Analysis:** Net Spent, Refunds, Merchant/Category breakdown.
  - **Cash Flow Analysis:** Tracks Deposits vs Withdrawals separate from Investments.
  - **Profit/Loss Proxy:** Tracks "Net Invested" (Cash Flow into Assets) vs Current Value (future todo).
  - Monthly breakdown of Card, Investment, and Cash Flow.
- **Iteration 6 (Refinement):** **Completed (2026-02-10).**
  - Improved WebSocket stability (timeout handling, connection checks, graceful error recovery).
  - Updated to use `timelineDetailV2` for fetching transaction details, matching the official app's behavior.
  - Added robust response filtering to ignore echo/heartbeat messages.
- **Iteration 7 (Spending Intelligence):** **Completed (2026-02-10).**
  - **Subscription Detection:** Heuristic algorithm to identify recurring monthly/yearly payments (Netflix, Spotify, etc.) and estimate monthly fixed costs.
  - **Robust Timestamp Parsing:** `PortfolioAnalyzer` now handles both numeric (millisecond) and ISO string timestamps seamlessly, improving testability and robustness against API changes.
  - **Enhanced Reporting:** New "Potential Subscriptions" section in the CLI report.
- **Iteration 8 (Visualization):** **Completed (2026-02-11).**
  - **ASCII Spending Chart:** Monthly spending trend visualization showing last 12 months as horizontal bar chart.
  - Clean formatting with abbreviated month labels and auto-scaling bars.
- **Iteration 9 (Spending Insights):** **Completed (2026-02-11).**
  - **Month-to-Date Projection:** Extrapolates current month spending based on daily pace.
  - **Year-over-Year Comparison:** Shows same month last year and % change.
  - **Savings Rate:** Calculates deposits vs spending ratio for the month.
  - **Pace Indicators:** Visual warnings (⚠️/✅) when spending pace is significantly above/below recent averages.
- **Iteration 10 (Budget & Weekly Subs):** **Completed (2026-02-11).**
  - **Weekly Subscription Detection:** Extended subscription heuristics to detect weekly recurring payments (5-9 day intervals).
  - **Budget Tracking:** New `--budget` CLI flag to set monthly spending limit with visual pace indicators (🟢🟡🔴).
- **Iteration 11 (Category Auto-Learning):** **Completed (2026-02-11).**
  - **Uncategorized Detection:** Identifies merchants tagged as "Other" with 2+ transactions.
  - **AI Category Suggestions:** Heuristic pattern matching suggests categories based on common keywords.
  - **Export Workflow:** New `--export-suggestions PATH` flag exports uncategorized merchants to CSV for review.
  - **Report Section:** "Uncategorized Merchants" section shows top 15 merchants needing categorization with suggested categories.
- **Iteration 12 (JSON Export & Budget History):** **Completed (2026-02-11).**
  - **JSON Export:** New `--format json` and `--json-output PATH` flags for programmatic access to all report data.
  - **Historical Budget Tracking:** New report section shows month-by-month budget adherence with visual indicators (🟢🟡🔴).
  - **Structured Data:** JSON output includes summary, spending by category, top merchants, subscriptions, monthly breakdown, and budget history.
- **Iteration 13 (Category Confidence Scores):** **Completed (2026-02-11).**
  - **Confidence Scoring:** AI category suggestions now include confidence scores (0.0-1.0) based on keyword specificity, match position, and name length.
  - **Visual Indicators:** Report displays confidence as ●●● (high ≥85%), ●●○ (medium ≥70%), ●○○ (low), ○○○ (none).
  - **Enhanced CSV Export:** Category suggestions CSV now includes Confidence and Reason columns for better review workflow.
  - **JSON Uncategorized:** JSON output now includes `uncategorized` array with full confidence metadata (`confidence`, `confidence_level`, `reason`).
- **Iteration 14 (Auto-Apply High Confidence):** **Completed (2026-02-11).**
  - **Auto-Categorize:** New `--auto-apply` flag automatically adds high-confidence suggestions to `data/categories.csv`.
  - **Configurable Threshold:** `--auto-apply-threshold` sets minimum confidence (default: 0.90 / 90%).
  - **Dry-Run Mode:** `--dry-run` previews changes without writing to CSV.
  - **Duplicate Detection:** Skips merchants already present in categories.csv.
- **Iteration 15 (Spending Alerts & Anomaly Detection):** **Completed (2026-02-11).**
  - **Anomaly Detection:** Automatic detection of unusual spending patterns.
  - **Alert Types:**
    - **Large Transactions:** Flags purchases >2x merchant average or >€150 first-time purchases.
    - **Daily Spending Spikes:** Detects days with >2.5x average spending.
    - **New Merchants:** Lists first-time merchants from the last 7 days.
    - **Category Overspending:** Alerts when category spending exceeds 80% of 3-month average.
  - **Alerts-Only Mode:** New `--alerts-only` flag shows only alerts (skip full report).
  - **JSON Support:** Alerts included in JSON output for integration with notification systems.
- **Iteration 16 (Category Goals):** **Completed (2026-02-11).**
  - **Per-Category Budget Limits:** Set monthly spending limits for individual categories (Food, Entertainment, Transport, etc.).
  - **Visual Progress Tracking:** Progress bars with status indicators (✅🟢🟡🔴) for each category.
  - **Projected Overspending Warnings:** Alerts when projected to exceed category limits.
  - **Goals CSV:** Configurable via `data/category_goals.csv`.
  - **CLI Integration:** New `--category-goals PATH` flag for custom goals file.
  - **JSON Support:** Category goals progress included in JSON output.

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run
export TR_PHONE="+4912345678"
export TR_PIN="1234"
python3 -m src.tracker.cli --output my_transactions.csv

# With budget tracking (EUR)
python3 -m src.tracker.cli --budget 2000 --output my_transactions.csv

# Export uncategorized merchants for review
python3 -m src.tracker.cli --input my_transactions.csv --export-suggestions uncategorized.csv
# Then: Edit uncategorized.csv, fill 'Category' column, append to data/categories.csv

# JSON output (for scripts/integrations)
python3 -m src.tracker.cli --input my_transactions.csv --format json
python3 -m src.tracker.cli --input my_transactions.csv --json-output report.json --budget 2000

# Auto-apply high-confidence category suggestions (≥90%)
python3 -m src.tracker.cli --input my_transactions.csv --auto-apply

# Preview what would be auto-applied (dry-run)
python3 -m src.tracker.cli --input my_transactions.csv --auto-apply --dry-run

# Custom threshold (e.g., 85%)
python3 -m src.tracker.cli --input my_transactions.csv --auto-apply --auto-apply-threshold 0.85

# View spending alerts only (quick check for anomalies)
python3 -m src.tracker.cli --input my_transactions.csv --alerts-only

# Alerts as JSON (for integrations/notifications)
python3 -m src.tracker.cli --input my_transactions.csv --alerts-only --format json

# Use custom category goals file
python3 -m src.tracker.cli --input my_transactions.csv --category-goals my_goals.csv
```

## Structure

- `src/tracker/client.py`: Core API client (Auth + WebSocket).
- `src/tracker/timeline.py`: Timeline management and processing.
- `src/tracker/analysis.py`: Logic for spending reports and profit/loss calculation.
- `src/tracker/cli.py`: Command-line interface.
