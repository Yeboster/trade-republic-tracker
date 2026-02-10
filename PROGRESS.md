[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 4 & 5 Complete. The Python tracker in `projects/trade-republic-tracker` now fully supports Auth, WebSocket streaming, Card Transaction filtering, and Spending Analysis (with Merchant Categorization). Logic verified via new unit tests.

**Status Update:**
1.  **Card Focus (Iteration 3 & 4):**
    -   Verified `card_successful_transaction` vs `ORDER_EXECUTED` distinction handling.
    -   Implemented `TimelineManager` to normalize fields (`merchant`, `spending_category`, `normalized_amount` which accounts for refunds).
    -   Added merchant-to-category mapping (CSV-driven) using `data/categories.csv`.
2.  **Analysis (Iteration 5):**
    -   Implemented `PortfolioAnalyzer`: Generates a report with Net Spending (Gross - Refunds), Top 10 Merchants, and Monthly Breakdown.
    -   Added "Net Invested" (Cash Flow) calculation for investments.
    -   **P/L Note:** Full "Unrealized P/L" requires instrument pricing history which is out of scope for transaction-only parsing, but "Net Invested" accurately tracks cash flows.
3.  **Verification:**
    -   Created `tests/test_logic.py` to verify filtering, normalization, and report generation without requiring live credentials.
    -   Tests confirm that refunds correctly offset spending in the "Net Spent" total.

**Next Steps:**
-   **User Testing:** Run `python3 -m src.tracker.cli` with real credentials to verify against live data.
-   **Refinement:** Improve WebSocket subscription handling (currently uses a basic timeout loop which may be fragile on slow connections).

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/`
-   Tests: `projects/trade-republic-tracker/tests/test_logic.py`
