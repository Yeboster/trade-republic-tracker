[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 19 (Merchant Name Normalization) Complete. Added merchant name cleaning for cleaner reports.

**Status Update:**
1.  **Merchant Normalization (Iteration 19):**
    -   **New `--normalize` Flag:** Cleans up messy merchant names in spending reports.
    -   **Features:**
        -   Removes store numbers/IDs ("LIDL #12345" → "Lidl")
        -   Removes location suffixes ("CARREFOUR PARIS 7E" → "Carrefour")
        -   100+ brand mappings (supermarkets, restaurants, tech, transport, etc.)
        -   Smart title case for unknown merchants
    -   **Debug Mode:** `--show-normalization` shows applied mappings.
    -   **New Module:** `src/tracker/normalize.py` with:
        -   `normalize_merchant()` - Single merchant normalization
        -   `MerchantNormalizer` - Stateful normalizer with caching
        -   `get_merchant_group()` - Aggressive grouping for aggregation
        -   Configurable brand mappings and strip patterns

2.  **Prior Work:**
    -   Iteration 18: Telegram digest & alerts integration.
    -   Iteration 17: Configurable thresholds & weekly trends.
    -   Iteration 16: Per-category budget goals.
    -   Iteration 15: Spending alerts & anomaly detection.
    -   Iterations 1-14: Core infrastructure (auth, WebSocket, timeline, analysis, insights, visualization).

**Next Steps:**
-   **HTML Reports:** Generate rich HTML reports with charts.
-   **API Endpoints:** Flask/FastAPI wrapper for web dashboard integration.
-   **Investment P&L:** Fetch current portfolio value for actual profit/loss calculation.
-   **Cron Job Setup:** Create OpenClaw cron job for daily/weekly spending notifications.
-   **Merchant Grouping:** Use normalization to aggregate similar merchants in reports.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/`
-   CLI: `python3 -m src.tracker.cli --help`
