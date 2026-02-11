[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 10 (Budget & Weekly Subs) Complete. Extended subscription detection to catch weekly recurring payments, and added budget tracking with visual pace indicators.

**Status Update:**
1.  **Weekly Subscription Detection (Iteration 10):**
    -   Extended `_subscription_section()` to detect 5-9 day intervals (weekly patterns).
    -   Weekly costs are converted to monthly equivalent (×4.33) for total subscription cost.
    -   Useful for detecting weekly gym classes, meal deliveries, etc.

2.  **Budget Tracking (Iteration 10):**
    -   New `--budget` CLI flag to set monthly spending limit.
    -   Budget Tracker section in report shows:
        -   Budget vs MTD spending
        -   Remaining amount and percentage
        -   Pace indicators (🟢🟡🔴) comparing actual vs expected usage
        -   Warning if projected to exceed budget

3.  **Prior Work (Iteration 9):**
    -   MTD Projection, YoY comparison, Savings Rate, Pace Indicators.

**Next Steps:**
-   **Category Auto-Learning:** Detect uncategorized merchants with high frequency and suggest categories.
-   **Export Formats:** Add JSON export option for programmatic use.
-   **Historical Budgets:** Track budget adherence over multiple months.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/analysis.py`
-   Tests: `projects/trade-republic-tracker/tests/test_logic.py`
