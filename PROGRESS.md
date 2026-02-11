[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 15 (Spending Alerts & Anomaly Detection) Complete. Added automatic detection of unusual spending patterns.

**Status Update:**
1.  **Spending Alerts Feature (Iteration 15):**
    -   **Anomaly Detection Engine:** New `_alerts_section()` method in `analysis.py` detects four types of spending anomalies:
        -   **Large Transactions:** Purchases >2x merchant average or >€150 first-time purchases.
        -   **Daily Spending Spikes:** Days with spending >2.5x daily average (minimum €200 threshold).
        -   **New Merchants:** First-time vendors seen in the last 7 days.
        -   **Category Overspending:** Categories exceeding 80% of 3-month historical average.
    -   **CLI Integration:** New `--alerts-only` flag for quick anomaly checks without full report.
    -   **JSON Support:** Alerts included in JSON output under `alerts` key for integrations.
    -   **Report Integration:** Alerts section appears automatically in standard reports when anomalies detected.

2.  **Implementation Details:**
    -   `analysis.py`: New `_alerts_section()`, `_format_date()`, and `get_alerts()` methods.
    -   `cli.py`: New `--alerts-only` argument with both text and JSON output modes.
    -   Uses statistical outlier detection (2x, 2.5x thresholds) with minimum absolute thresholds to avoid noise.

3.  **Prior Work:**
    -   Iteration 14: Auto-apply high-confidence category suggestions.
    -   Iteration 13: Confidence scoring system.
    -   Iteration 12: JSON export, historical budget tracking.
    -   Iteration 11: Category auto-learning, AI suggestions.
    -   Iterations 1-10: Core infrastructure (auth, WebSocket, timeline, analysis, insights).

**Next Steps:**
-   **Notification Integration:** Connect alerts to Telegram/push notifications.
-   **Alert Thresholds:** Make detection thresholds configurable via CLI flags.
-   **Trend Analysis:** Add week-over-week and month-over-month spending trends.
-   **API Endpoints:** Flask/FastAPI wrapper for web dashboard integration.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/`
-   CLI: `python3 -m src.tracker.cli --help`
