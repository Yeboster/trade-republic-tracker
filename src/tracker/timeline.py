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

    def filter_card_transactions(self) -> List[Dict]:
        """
        Filters the raw transactions for card events.
        """
        card_txns = []
        # Filter for relevant event types
        # card_successful_transaction: Spending
        # card_refund: Refund
        # card_failed_transaction: Failed
        
        relevant_types = [
            'card_successful_transaction',
            'card_refund',
            'card_failed_transaction'
        ]
        
        for txn in self.transactions:
            event_type = txn.get('eventType')
            if event_type in relevant_types:
                # Enhance transaction with normalized data
                normalized = self._normalize_card_transaction(txn)
                card_txns.append(normalized)
                 
        return card_txns

    def _normalize_card_transaction(self, txn: Dict) -> Dict:
        """
        Adds convenience fields to the transaction dict.
        """
        # Create a copy to avoid mutating original if that matters (shallow copy fine)
        t = txn.copy()
        
        event_type = t.get('eventType')
        title = t.get('title', 'Unknown')
        amount_data = t.get('amount', {})
        val = amount_data.get('value', 0.0)
        currency = amount_data.get('currency', 'EUR')
        
        # Determine normalized amount (signed)
        # Assumption: API returns absolute value.
        # Spending -> Negative
        # Refund -> Positive
        
        signed_amount = val
        if event_type == 'card_successful_transaction':
            signed_amount = -abs(val)
        elif event_type == 'card_refund':
            signed_amount = abs(val)
        elif event_type == 'card_failed_transaction':
            signed_amount = 0.0 # Or keep it as is but mark status?
            
        t['normalized_amount'] = signed_amount
        t['merchant'] = title # Title is usually the merchant name
        t['currency'] = currency
        
        return t

    def export_to_csv(self, filename: str):
        card_txns = self.filter_card_transactions()
        
        if not card_txns:
            logger.warning("No card transactions to export.")
            return

        # Define CSV columns
        fieldnames = [
            "id",
            "timestamp",
            "merchant",
            "normalized_amount",
            "currency",
            "status",
            "eventType",
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
                "eventType": t.get("eventType"),
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
