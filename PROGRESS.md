[TRADE REPUBLIC RESEARCH]

**Summary:**
I have successfully ported and improved the Trade Republic tracker in `projects/trade-republic-tracker`. Code is ready for user testing.
Logic for Card Transactions and Spending Analysis has been **verified with unit tests**.

**Work Completed (All Iterations):**
1.  **Authentication:** Implemented a robust `TradeRepublicClient` handling Login, OTP verification, and Session Refresh using `httpx`.
2.  **WebSocket Protocol:** Implemented the WebSocket handshake (`connect 31 ...`) and subscription mechanism (`sub ID Payload`) using `websockets`.
3.  **Transaction History:** Implemented `TimelineManager` to fetch full transaction history via WebSocket pagination (`timelineTransactions`).
4.  **Card Focus:** 
    - Verified against Go reference `tests/fakes` and new Python `tests/test_logic.py`.
    - Implemented specific filtering for `card_successful_transaction` (Spending).
    - Mapped `title` to Merchant Name.
    - Fixed timestamp ISO parsing.
5.  **Analysis & Reporting:** 
    - Added `SpendingAnalyzer` to generate summary reports.
    - **Refined (2026-02-10):** Top Merchants now calculate **Net Spending** (Spending - Refunds). Returns/Refunds correctly reduce the merchant's share.
    - Added `tests/test_logic.py` to ensure logic correctness without live credentials.

**Codebase:**
- Location: `projects/trade-republic-tracker/`
- Entry point: `python3 -m src.tracker.cli`
- Tests: `python3 projects/trade-republic-tracker/tests/test_logic.py`

**Next Steps:**
- User testing with real credentials (interactive mode).
- Verify "Profit/Loss" calculation against app UI to ensure currency direction (negative vs positive) holds true for all edge cases (Type: 'card_refund', etc.).
