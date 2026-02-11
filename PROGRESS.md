[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 12 (JSON Export & Budget History) Complete. Added structured JSON export for programmatic use and historical budget tracking.

**Status Update:**
1.  **JSON Export (Iteration 12):**
    -   New `--format json` CLI flag outputs structured JSON instead of text.
    -   New `--json-output PATH` writes JSON to file (implies `--format json`).
    -   JSON includes: summary, spending by category, top merchants, subscriptions, monthly breakdown, and budget history.

2.  **Historical Budget Tracking (Iteration 12):**
    -   New report section "BUDGET HISTORY (Last 6 Months)" when `--budget` is set.
    -   Shows month-by-month spending vs budget with visual indicators (🟢🟡🔴).
    -   Summarizes over-budget months with total overage amount.
    -   Also included in JSON output under `budget.history`.

3.  **Prior Work:**
    -   Iteration 11: Category auto-learning, AI suggestions, export workflow.
    -   Iteration 10: Budget tracking, weekly subscription detection.
    -   Iteration 9: MTD Projection, YoY comparison, Savings Rate.

**Next Steps:**
-   **API Endpoints:** Add Flask/FastAPI wrapper for web dashboard integration.
-   **Category Confidence Scores:** Show confidence level for AI suggestions.
-   **Alerts/Notifications:** Integration with notification systems for budget alerts.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/analysis.py`
-   CLI: `projects/trade-republic-tracker/src/tracker/cli.py`
