import csv
import json
from datetime import datetime
from api.models import Transaction

class CsvExporter:
    def __init__(self, filename="transactions.csv"):
        self.filename = filename

    def export(self, transactions):
        if not transactions:
            print("No transactions to export.")
            return

        # Prepare CSV headers
        headers = [
            "Date",
            "Type",
            "Title",
            "Subtitle",
            "Amount",
            "Currency",
            "Status",
            "Icon",
            "ID",
            "Details"  # New column for JSON details
        ]

        card_transactions = [tx for tx in transactions if tx.is_card_transaction]
        
        print(f"Exporting {len(transactions)} total transactions ({len(card_transactions)} card transactions)...")

        with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for tx in transactions:
                writer.writerow(self._parse_row(tx))
                
        # Export card transactions separately
        card_filename = f"card_{self.filename}"
        with open(card_filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for tx in card_transactions:
                writer.writerow(self._parse_row(tx))
                
        print(f"Export complete: {self.filename} and {card_filename}")

    def _parse_row(self, tx: Transaction):
        details_json = ""
        if tx.details:
            try:
                details_json = json.dumps(tx.details)
            except:
                details_json = "Error serializing details"
                
        return {
            "Date": self._format_date(tx.timestamp),
            "Type": tx.event_type,
            "Title": tx.title,
            "Subtitle": tx.subtitle,
            "Amount": tx.amount,
            "Currency": tx.currency,
            "Status": tx.status,
            "Icon": tx.icon,
            "ID": tx.id,
            "Details": details_json
        }

    def _format_date(self, timestamp):
        try:
            # Try to convert if it looks like an int/float
            ts = float(timestamp)
            # Check if ms or sec
            if ts > 1000000000000: # ms
                return datetime.fromtimestamp(ts / 1000).isoformat()
            return datetime.fromtimestamp(ts).isoformat()
        except (ValueError, TypeError):
            # Maybe it's already a string date
            return timestamp
