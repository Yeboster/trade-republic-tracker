from collections import defaultdict
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SpendingAnalyzer:
    def __init__(self, transactions: List[Dict]):
        self.transactions = transactions

    def generate_report(self) -> str:
        """
        Generates a text summary of spending/income.
        """
        if not self.transactions:
            return "No transactions to analyze."

        total_income = 0.0
        total_spending = 0.0
        by_month = defaultdict(lambda: {"in": 0.0, "out": 0.0})
        by_merchant = defaultdict(float)

        currency = "EUR" 

        for txn in self.transactions:
            # Prefer normalized amount if available
            if 'normalized_amount' in txn:
                val = txn['normalized_amount']
            else:
                # Fallback for raw data
                amount_data = txn.get('amount', {})
                val = amount_data.get('value', 0.0)
                # Apply heuristic if raw
                if txn.get('eventType') == 'card_successful_transaction':
                    val = -abs(val)
                elif txn.get('eventType') == 'card_refund':
                    val = abs(val)
                # Else assume signed as is

            cur = txn.get('currency', txn.get('amount', {}).get('currency', 'EUR'))
            
            # Skip failed/cancelled if status present and not executed
            status = txn.get('status')
            if status and status.upper() not in ['EXECUTED', 'CONFIRMED']:
                continue

            try:
                val = float(val)
            except (ValueError, TypeError):
                continue

            merchant = txn.get('merchant', txn.get('title', 'Unknown'))
            
            # Net Merchant Tracking
            # Spending is negative val, Refund is positive val.
            # We want "Amount Spent" to be positive for the table, so we invert `val`.
            # If val is -20 (spend), we add 20 to 'spent'.
            # If val is +20 (refund), we add -20 to 'spent' (reducing it).
            by_merchant[merchant] += (-val)

            if val < 0:
                amount = abs(val)
                total_spending += amount
                month = self._get_month(txn)
                by_month[month]["out"] += amount
            else:
                total_income += val
                month = self._get_month(txn)
                by_month[month]["in"] += val

            currency = cur

        # Sort merchants by Net Spend (descending)
        # Filter out merchants with <= 0 spend (net refunds or zero) for the "Top Spenders" list
        top_merchants = sorted(
            [(m, a) for m, a in by_merchant.items() if a > 0], 
            key=lambda x: x[1], 
            reverse=True
        )[:5]

        report = []
        report.append(f"=== Spending Analysis ({currency}) ===")
        report.append(f"Total Spent: {total_spending:.2f}")
        report.append(f"Total Income/Refunds: {total_income:.2f}")
        report.append(f"Net: {total_income - total_spending:.2f}")
        report.append("")
        report.append("--- Monthly Breakdown ---")
        for month in sorted(by_month.keys()):
            m_data = by_month[month]
            report.append(f"{month}: Spent {m_data['out']:.2f} | Refund {m_data['in']:.2f}")
        
        report.append("")
        report.append("--- Top 5 Merchants ---")
        for merchant, amount in top_merchants:
            report.append(f"{merchant}: {amount:.2f}")
            
        return "\n".join(report)

    def _get_month(self, txn) -> str:
        ts = txn.get('timestamp')
        try:
            if isinstance(ts, (int, float)):
                if ts > 10**11: 
                    dt = datetime.fromtimestamp(ts / 1000)
                else:
                    dt = datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                # Handle 2024-05-27T13:51:55.167+0000 format
                if "+" in ts:
                    # simplistic fix for ISO +0000
                    ts = ts.replace("+0000", "+00:00")
                
                # Check for Z
                ts = ts.replace('Z', '+00:00')
                
                dt = datetime.fromisoformat(ts)
            else:
                return "Unknown"
            return dt.strftime("%Y-%m")
        except Exception as e:
            # logger.debug(f"Failed to parse timestamp {ts}: {e}")
            return "Unknown"
