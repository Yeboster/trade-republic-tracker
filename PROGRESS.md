[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 8 (Visualization) Complete. Added ASCII bar chart for monthly card spending trends, making it easier to spot spending patterns at a glance.

**Status Update:**
1.  **ASCII Spending Chart (Iteration 8):**
    -   Added `_spending_chart()` method to `PortfolioAnalyzer`.
    -   Shows last 12 months of card spending as horizontal bar chart.
    -   Clean formatting with month labels (e.g., "Jan'24") and EUR amounts.
    -   Auto-scales bars based on max spending in the period.
2.  **Prior Work (Iteration 7):**
    -   Subscription Detection: Groups transactions by merchant, checks for consistent amounts (+/- 10%) and regular intervals (monthly/yearly).
    -   Reporting: "Potential Subscriptions" section with frequency and estimated monthly cost.
    -   Robust timestamp handling (milliseconds and ISO strings).

**Next Steps:**
-   **User Testing:** Run against real data to validate subscription heuristics.
-   **Weekly Detection:** Extend subscription detection to weekly recurring payments.
-   **Category Refinement:** Continue refining `data/categories.csv` based on real merchant names.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/analysis.py`
-   Tests: `projects/trade-republic-tracker/tests/test_logic.py`
