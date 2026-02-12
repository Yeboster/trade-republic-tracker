[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 18 (Telegram Integration) Complete. Added Telegram-formatted output for spending digests and alerts.

**Status Update:**
1.  **Telegram Digest (Iteration 18):**
    -   **New `--telegram-digest` Flag:** Outputs a comprehensive spending summary formatted for Telegram (HTML).
    -   **Content Includes:**
        -   Month-to-date spending with projected total
        -   Budget status (if set) with visual indicators
        -   Weekly trend with WoW change
        -   Category goal alerts (over-budget categories)
        -   Spending alerts summary (categorized)
    -   **Telegram-Friendly Formatting:** Uses `<b>`, `<code>`, `<i>` tags supported by Telegram.

2.  **Telegram Alerts-Only Mode:**
    -   **New `--telegram-alerts` Flag:** Outputs only alerts (silent if none).
    -   **Minimal Format:** Just the critical alerts, no summary fluff.
    -   **Use Case:** Daily automated checks that only notify when there's something worth seeing.

3.  **Alert Threshold:**
    -   **New `--telegram-threshold N` Flag:** Only generates output if N or more alerts detected.
    -   **Reduces Noise:** Skip notifications on quiet days.

4.  **OpenClaw Integration:**
    -   Output designed to be captured and sent via OpenClaw's messaging system.
    -   Can be used in cron jobs for automated daily/weekly spending reports.

5.  **Prior Work:**
    -   Iteration 17: Configurable thresholds & weekly trends.
    -   Iteration 16: Per-category budget goals.
    -   Iteration 15: Spending alerts & anomaly detection.
    -   Iterations 1-14: Core infrastructure (auth, WebSocket, timeline, analysis, insights, visualization).

**Next Steps:**
-   **HTML Reports:** Generate rich HTML reports with charts.
-   **API Endpoints:** Flask/FastAPI wrapper for web dashboard integration.
-   **Investment P&L:** Fetch current portfolio value for actual profit/loss calculation.
-   **Cron Job Setup:** Create OpenClaw cron job for daily/weekly spending notifications.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/`
-   CLI: `python3 -m src.tracker.cli --help`
