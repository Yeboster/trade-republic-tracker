import csv
import logging
from typing import List, Dict

from .categories import categorize_merchant

logger = logging.getLogger(__name__)


# Investment subtitles that identify non-card transactions
INVESTMENT_SUBTITLES = {
    "buy order", "sell order", "saving executed", "saveback",
    "round up", "pea", "dividend", "interest", "deposit",
    "withdrawal", "transfer", "tax", "fee",
}


class TimelineManager:
    def __init__(self, client):
        self.client = client
        self.transactions = []

    async def fetch_transactions(self, limit: int = 0):
        self.transactions = await self.client.fetch_timeline_transactions(limit)
        return self.transactions

    # ── Classification ──────────────────────────────────────────────

    @staticmethod
    def classify(txn: Dict) -> str:
        """
        Returns one of: 'card', 'investment', 'transfer_in', 'transfer_out', 'other'.
        
        Uses 'eventType' from JSON if available (most reliable),
        falling back to icon/subtitle heuristics.
        """
        event_type = txn.get("eventType") or ""
        icon = txn.get("icon") or ""
        subtitle = (txn.get("subtitle") or "").strip().lower()
        title = (txn.get("title") or "").strip().lower()
        cash_account = txn.get("cashAccountNumber")
        amount_val = (txn.get("amount") or {}).get("value", 0)

        # 1. Strong signal: eventType
        if event_type in ("card_successful_transaction", "card_failed_transaction", "card_refund", "card_successful_verification"):
            return "card"
        
        if event_type in ("PAYMENT_INBOUND", "PAYMENT_INBOUND_SEPA_DIRECT_DEBIT", "INCOMING_TRANSFER", "INCOMING_TRANSFER_DELEGATION", "CREDIT"):
            return "transfer_in"
            
        if event_type in ("PAYMENT_OUTBOUND", "OUTGOING_TRANSFER_DELEGATION"):
            return "transfer_out"
        
        if event_type in (
            "ORDER_EXECUTED", 
            "SAVINGS_PLAN_EXECUTED", 
            "SAVINGS_PLAN_INVOICE_CREATED", 
            "INTEREST_PAYOUT", 
            "INTEREST_PAYOUT_CREATED", 
            "DIVIDEND_PAYOUT",
            "trading_savingsplan_executed",
            "ssp_corporate_action_invoice_cash",
            "TRADE_INVOICE",
            "benefits_saveback_execution",
            "benefits_spare_change_execution",
            "timeline_legacy_migrated_events" # Often old trades
        ):
            return "investment"

        # 2. Strong signal: merchant icon
        if "merchant-" in icon:
            return "card"

        # 3. Heuristics for older/incomplete data

        # Explicit transfer keywords in title/subtitle
        if "transfer" in title or "transfer" in subtitle:
            if amount_val > 0:
                return "transfer_in"
            else:
                return "transfer_out"
                
        if "deposit" in title or "deposit" in subtitle:
             return "transfer_in"
             
        if "withdrawal" in title or "withdrawal" in subtitle:
             return "transfer_out"

        # Investment: known subtitles
        if subtitle and any(s in subtitle for s in INVESTMENT_SUBTITLES):
            return "investment"

        # Investment: has cashAccountNumber (brokerage account reference usually)
        if cash_account:
            return "investment"

        # Heuristic fallback: no subtitle + no cash account + negative = card
        if not subtitle and cash_account is None and amount_val < 0:
            return "card"

        return "other"

    # ── Filters ─────────────────────────────────────────────────────

    def filter_card_transactions(self) -> List[Dict]:
        return [self._normalize(t, "card") for t in self.transactions if self.classify(t) == "card"]

    def filter_investment_transactions(self) -> List[Dict]:
        return [self._normalize(t, "investment") for t in self.transactions if self.classify(t) == "investment"]

    def filter_all_classified(self) -> List[Dict]:
        """Returns all transactions with a 'category' field added."""
        return [self._normalize(t, self.classify(t)) for t in self.transactions]

    # ── Normalization ───────────────────────────────────────────────

    @staticmethod
    def _normalize(txn: Dict, category: str) -> Dict:
        t = txn.copy()
        amount_data = t.get("amount", {})
        val = amount_data.get("value", 0.0)
        currency = amount_data.get("currency", "EUR")

        t["normalized_amount"] = val  # API already signs values
        t["merchant"] = t.get("title", "Unknown")
        t["currency"] = currency
        t["category"] = category
        t["subtitle_raw"] = t.get("subtitle") or ""
        t["event_type"] = t.get("eventType") or ""
        
        # Add spending category for card transactions
        if category == "card":
            t["spending_category"] = categorize_merchant(t["merchant"])
        else:
            t["spending_category"] = ""
            
        # Add timestamp parsing for better sorting/filtering
        ts = t.get("timestamp")
        if ts:
            # Simple ISO parse if possible, else keep string
            t["timestamp_iso"] = ts
        
        return t

    # ── Export ───────────────────────────────────────────────────────

    def export_to_csv(self, filename: str, categories: List[str] = None):
        """
        Export transactions to CSV. 
        categories: filter to specific categories, e.g. ['card', 'investment'].
        None = export all.
        """
        all_txns = self.filter_all_classified()
        
        if categories:
            all_txns = [t for t in all_txns if t["category"] in categories]

        if not all_txns:
            logger.warning("No transactions to export.")
            return

        fieldnames = [
            "id", "timestamp", "category", "spending_category", "merchant",
            "normalized_amount", "currency", "status",
            "subtitle_raw", "title", "event_type"
        ]

        rows = [{k: t.get(k) for k in fieldnames} for t in all_txns]

        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
            logger.info(f"Exported {len(rows)} transactions to {filename}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
