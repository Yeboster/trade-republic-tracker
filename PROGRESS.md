[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 14 (Auto-Apply High Confidence) Complete. Added automatic categorization of high-confidence merchant suggestions.

**Status Update:**
1.  **Auto-Apply Feature (Iteration 14):**
    -   New `--auto-apply` CLI flag automatically writes high-confidence suggestions to `data/categories.csv`.
    -   Configurable threshold via `--auto-apply-threshold` (default: 0.90).
    -   `--dry-run` mode previews changes without modifying files.
    -   Duplicate detection prevents adding merchants already in the CSV.
    -   Clean output shows each auto-applied rule with confidence score and reason.

2.  **Implementation Details:**
    -   `categories.py`: Added `append_rules_to_csv()` function with duplicate detection.
    -   `analysis.py`: Added `get_high_confidence_suggestions()` method.
    -   `cli.py`: New argument parsing and auto-apply workflow (runs before export/analysis).

3.  **Prior Work:**
    -   Iteration 13: Confidence scoring system.
    -   Iteration 12: JSON export, historical budget tracking.
    -   Iteration 11: Category auto-learning, AI suggestions.
    -   Iterations 1-10: Core infrastructure (auth, WebSocket, timeline, analysis, insights).

**Next Steps:**
-   **API Endpoints:** Flask/FastAPI wrapper for web dashboard integration.
-   **Alerts/Notifications:** Integration with notification systems for budget alerts.
-   **Category Learning:** Use transaction frequency/amount patterns to improve suggestions.
-   **Historical Comparison:** "Spending vs. Same Period Last Year" detailed view.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/`
-   CLI: `python3 -m src.tracker.cli --help`
