[TRADE REPUBLIC RESEARCH]

**Summary:**
Iteration 13 (Category Confidence Scores) Complete. Enhanced AI category suggestions with confidence scoring system.

**Status Update:**
1.  **Confidence Scoring (Iteration 13):**
    -   AI category suggestions now return a confidence score (0.0-1.0).
    -   Scoring factors: keyword specificity, match position (start = higher), keyword length, merchant name length.
    -   Pattern weights refined: specific terms (e.g., "ristorante", "pharmacie") get higher base confidence than generic ones ("shop", "store").
    -   Known brands (Netflix, Uber, Shell) get near-perfect confidence (~0.95-0.98).

2.  **Visual Confidence Indicators:**
    -   Report shows confidence as: ●●● (≥85%), ●●○ (≥70%), ●○○ (>0%), ○○○ (no suggestion).
    -   Helps users prioritize which suggestions to trust vs. review manually.

3.  **Enhanced Exports:**
    -   CSV export now includes `Confidence` and `Reason` columns.
    -   Sorted by confidence (highest first), then by total spent.
    -   JSON output includes `uncategorized` array with full metadata: `confidence`, `confidence_level`, `reason`.

4.  **Prior Work:**
    -   Iteration 12: JSON export, historical budget tracking.
    -   Iteration 11: Category auto-learning, AI suggestions, export workflow.
    -   Iteration 10: Budget tracking, weekly subscription detection.

**Next Steps:**
-   **Auto-Apply High Confidence:** Option to auto-categorize merchants with confidence ≥ 0.90.
-   **API Endpoints:** Flask/FastAPI wrapper for web dashboard integration.
-   **Alerts/Notifications:** Integration with notification systems for budget alerts.

**Links:**
-   Code: `projects/trade-republic-tracker/src/tracker/analysis.py`
-   CLI: `projects/trade-republic-tracker/src/tracker/cli.py`
