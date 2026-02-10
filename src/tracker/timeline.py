import csv
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TimelineManager:
    def __init__(self, client):
        self.client = client
        self.transactions = []

    async def fetch_transactions(self, limit: int = 100):
        self.transactions = await self.client.fetch_timeline_transactions(limit)
        return self.transactions

    def _is_card_transaction(self, txn: Dict) -> bool:
        """
        Identifies card (merchant) transactions from the timeline.
        
        Card transactions have:
        - icon containing "merchant-"
        - No subtitle (None)
        - cashAccountNumber is None
        
        Investments have ISINs in icon, subtitles like "Buy Order", 
        "Saving executed", "Saveback", "Round up", "Sell Order", "PEA".
        """
        icon = txn.get("icon") or ""
        subtitle = txn.get("subtitle")
        
        # Primary signal: merchant icon
        if "merchant-" in icon:
            return True
        
        # If no icon match, use heuristic:
        # No subtitle + no cashAccountNumber + negative amount = likely card spend
        if subtitle is None and txn.get("cashAccountNumber") is None:
            amount_val = (txn.get("amount") or {}).get("value", 0)
            if amount_val < 0:
                return True
        
        return False

    def _is_card_refund(self, txn: Dict) -> bool:
        """
        Identifies card refunds. Refunds have positive amounts
        and merchant icons.
        """
        icon = txn.get("icon") or ""
        amount_val = (txn.get("amount") or {}).get("value", 0)
        
        if "merchant-" in icon and amount_val > 0:
            return True
        
        return False

    def filter_card_transactions(self) -> List[Dict]:
        """
        Filters the raw transactions for card events (spending + refunds).
        """
        card_txns = []
        
        for txn in self.transactions:
            is_card = self._is_card_transaction(txn)
            is_refund = self._is_card_refund(txn)
            
            if is_card or is_refund:
                normalized = self._normalize_card_transaction(txn, is_refund=is_refund)
                card_txns.append(normalized)
                 
        return card_txns

    def _normalize_card_transaction(self, txn: Dict, is_refund: bool = False) -> Dict:
        """
        Adds convenience fields to the transaction dict.
        """
        t = txn.copy()
        
        title = t.get('title', 'Unknown')
        amount_data = t.get('amount', {})
        val = amount_data.get('value', 0.0)
        currency = amount_data.get('currency', 'EUR')
        
        # The API returns signed values already:
        # Spending: negative (e.g. -18.28)
        # Refunds: positive
        t['normalized_amount'] = val
        t['merchant'] = title
        t['currency'] = currency
        t['tx_type'] = 'refund' if is_refund else 'spending'
        
        return t

    def export_to_csv(self, filename: str):
        card_txns = self.filter_card_transactions()
        
        if not card_txns:
            logger.warning("No card transactions to export.")
            return

        fieldnames = [
            "id",
            "timestamp",
            "merchant",
            "normalized_amount",
            "currency",
            "status",
            "tx_type",
            "title"
        ]
        
        rows = []
        for t in card_txns:
            row = {
                "id": t.get("id"),
                "timestamp": t.get("timestamp"),
                "merchant": t.get("merchant"),
                "normalized_amount": t.get("normalized_amount"),
                "currency": t.get("currency"),
                "status": t.get("status"),
                "tx_type": t.get("tx_type"),
                "title": t.get("title")
            }
            rows.append(row)

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"Exported {len(rows)} card transactions to {filename}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
