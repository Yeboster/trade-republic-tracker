import unittest
import asyncio
import os
import json
from src.tracker.timeline import TimelineManager
from src.tracker.analysis import SpendingAnalyzer

class MockClient:
    async def fetch_timeline_transactions(self, limit: int = 100):
        # Return mock data
        return [
            {
                "id": "1",
                "timestamp": "2024-05-27T10:00:00.000+0000",
                "eventType": "card_successful_transaction",
                "title": "Starbucks",
                "amount": {"value": 5.50, "currency": "EUR"},
                "status": "EXECUTED"
            },
            {
                "id": "2",
                "timestamp": "2024-05-26T10:00:00.000+0000",
                "eventType": "card_successful_transaction",
                "title": "Amazon",
                "amount": {"value": 20.00, "currency": "EUR"},
                "status": "EXECUTED"
            },
            {
                "id": "3",
                "timestamp": "2024-05-25T10:00:00.000+0000",
                "eventType": "card_refund",
                "title": "Amazon",
                "amount": {"value": 20.00, "currency": "EUR"},
                "status": "EXECUTED"
            },
            { # Should be ignored (Investment)
                "id": "4",
                "timestamp": "2024-05-24T10:00:00.000+0000",
                "eventType": "order_buy",
                "title": "Apple Stock",
                "amount": {"value": 150.00, "currency": "EUR"},
                "status": "EXECUTED"
            },
            { # Failed transaction
                "id": "5",
                "timestamp": "2024-05-24T12:00:00.000+0000",
                "eventType": "card_failed_transaction",
                "title": "Suspicious Shop",
                "amount": {"value": 1000.00, "currency": "EUR"},
                "status": "FAILED"
            }
        ]

class TestTrackerLogic(unittest.TestCase):
    def setUp(self):
        self.mock_client = MockClient()
        self.tm = TimelineManager(self.mock_client)

    def test_filter_card_transactions(self):
        # We need to run the async fetch first
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.tm.transactions = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        filtered = self.tm.filter_card_transactions()
        
        # Expect 4 items (1 spending, 1 spending, 1 refund, 1 failed)
        # item 4 is order_buy, should be gone.
        self.assertEqual(len(filtered), 4) 
        
        ids = [t['id'] for t in filtered]
        self.assertIn("1", ids)
        self.assertIn("2", ids)
        self.assertIn("3", ids)
        self.assertIn("5", ids)
        self.assertNotIn("4", ids)

        # Check normalization
        t1 = next(t for t in filtered if t['id'] == "1")
        self.assertEqual(t1['normalized_amount'], -5.50)
        self.assertEqual(t1['merchant'], "Starbucks")
        
        t3 = next(t for t in filtered if t['id'] == "3")
        self.assertEqual(t3['normalized_amount'], 20.00)

    def test_spending_analysis(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        txns = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        # Pre-process using the same logic as the real app
        # But wait, SpendingAnalyzer takes raw transactions or filtered?
        # The CLI passes `tm.filter_card_transactions()` to analyzer usually?
        # Let's check how the analyzer is built. It expects normalized data for best results 
        # but has fallbacks for raw.
        # But `TimelineManager.filter_card_transactions` adds `normalized_amount`.
        # So we should pass the output of filter_card_transactions to be safe.
        
        self.tm.transactions = txns
        card_txns = self.tm.filter_card_transactions()
        
        analyzer = SpendingAnalyzer(card_txns)
        report = analyzer.generate_report()
        
        # Starbucks: -5.50
        # Amazon: -20.00
        # Amazon Refund: +20.00
        # Suspicious: 0 (FAILED status -> excluded by analyzer if we look at code)
        
        # Total Spent: 25.50
        # Total Income: 20.00
        # Net: -5.50
        
        print("\n--- Test Report Output ---\n" + report + "\n--------------------------")
        
        self.assertIn("Total Spent: 25.50", report)
        self.assertIn("Total Income/Refunds: 20.00", report)
        self.assertIn("Net: -5.50", report)
        
        # Check merchants
        self.assertIn("Starbucks: 5.50", report)
        # Amazon net? No, analyzer sums NET spending by merchant.
        # Amazon spent 20.00. Refund 20.00. Net 0.
        # So it should NOT appear in the list (filtered > 0).
        self.assertNotIn("Amazon: 20.00", report) # Amazon is net 0
        self.assertIn("Starbucks: 5.50", report) # Starbucks is net 5.50

    def test_csv_export(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.tm.transactions = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        filename = "test_output.csv"
        self.tm.export_to_csv(filename)
        
        self.assertTrue(os.path.exists(filename))
        
        with open(filename, 'r') as f:
            content = f.read()
            # Check headers
            self.assertIn("merchant,normalized_amount,currency,status,eventType", content)
            # Check rows
            self.assertIn("Starbucks,-5.5", content)
            self.assertIn("Amazon,20.0", content) # Refund (pos) or Spend (neg)? 
            # 20.0 is likely the refund or the spend (if formatted absolute? No, normalized is signed).
            # Wait, 20.0 could be the refund. Spend would be -20.0.
            
        os.remove(filename)

if __name__ == '__main__':
    unittest.main()
