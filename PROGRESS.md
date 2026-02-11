[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 17 (Configurable Thresholds & Weekly Trends) Complete. Added configurable alert thresholds and week-over-week spending trend analysis.

**Status Update:**
1.  **Configurable Alert Thresholds (Iteration 17):**
    -   **New `AlertThresholds` Class:** Encapsulates all detection thresholds for anomaly alerts.
    -   **CLI Flags:** Six new flags to customize sensitivity:
        -   `--threshold-large-first EUR` (default: 150)
        -   `--threshold-large-mult X` (default: 2.0)
        -   `--threshold-daily-mult X` (default: 2.5)
        -   `--threshold-daily-min EUR` (default: 200)
        -   `--threshold-cat-mult X` (default: 1.8)
        -   `--threshold-new-days DAYS` (default: 7)
    -   Allows users to tune alerts to their spending patterns.

2.  **Week-over-Week Trend Analysis:**
    -   **New Report Section:** `_weekly_trends_section()` shows last 4 weeks of spending.
    -   **Spending Velocity:** Compares recent 2 weeks vs prior 2 weeks to detect acceleration/deceleration.
    -   **WoW Change:** Percentage change from previous week with visual indicators (🔴🟡🟢).
    -   **4-Week Rolling Average:** Shows average weekly spending.
    -   **Transaction Counts:** Displays number of transactions per week.

3.  **JSON Support:**
    -   Weekly trends included in JSON output under `weekly_trends` key.
    -   Each entry includes: year, week, spend, count, wow_change.

4.  **Prior Work:**
    -   Iteration 16: Per-category budget goals with progress tracking.
    -   Iteration 15: Spending alerts & anomaly detection.
    -   Iteration 14: Auto-apply high-confidence category suggestions.
    -   Iterations 1-13: Core infrastructure (auth, WebSocket, timeline, analysis, insights, visualization).

**Next Steps:**
-   **Notification Integration:** Connect alerts to Telegram/push notifications.
-   **HTML Reports:** Generate rich HTML reports with charts.
-   **API Endpoints:** Flask/FastAPI wrapper for web dashboard integration.
-   **Investment P&L:** Fetch current portfolio value for actual profit/loss calculation.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/`
-   CLI: `python3 -m src.tracker.cli --help`
