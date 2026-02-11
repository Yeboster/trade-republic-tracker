[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 11 (Category Auto-Learning) Complete. Added automatic detection of uncategorized merchants and AI-suggested categories based on keyword patterns.

**Status Update:**
1.  **Uncategorized Merchant Detection (Iteration 11):**
    -   New `_uncategorized_section()` in report identifies merchants with "Other" category.
    -   Only shows merchants with 2+ transactions (recurring/significant).
    -   Sorted by total spending to prioritize high-value categorizations.

2.  **AI Category Suggestions (Iteration 11):**
    -   `_suggest_category()` method uses keyword pattern matching.
    -   Recognizes patterns for: Restaurant, Grocery, Shopping, Health, Transport, Entertainment, Travel, Services, Subscription, Utilities.
    -   Multi-language support (English, French, Italian, German, Slovak keywords).

3.  **Export Workflow (Iteration 11):**
    -   New `--export-suggestions PATH` CLI flag.
    -   Exports CSV with columns: Merchant, Category (blank), Transactions, TotalSpent, Suggested.
    -   User reviews, fills in Category column, appends to `data/categories.csv`.

4.  **Prior Work:**
    -   Iteration 10: Budget tracking, weekly subscription detection.
    -   Iteration 9: MTD Projection, YoY comparison, Savings Rate.

**Next Steps:**
-   **Export Formats:** Add JSON export option for programmatic use.
-   **Historical Budgets:** Track budget adherence over multiple months.
-   **Category Confidence Scores:** Show confidence level for AI suggestions.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/analysis.py`
-   CLI: `projects/trade-republic-tracker/src/tracker/cli.py`
