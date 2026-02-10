import unittest
import asyncio
import os
import json
import logging
from src.tracker.timeline import TimelineManager
from src.tracker.analysis import PortfolioAnalyzer

# Disable logging during tests
logging.disable(logging.CRITICAL)

class MockClient:
    async def fetch_timeline_transactions(self, limit: int = 100):
        # Return mock data matching real API structure
        return [
            {
                "id": "1",
                "timestamp": "2024-05-27T10:00:00.000+0000",
                "icon": "merchant-starbucks",
                "subtitle": "Berlin",
                "title": "Starbucks",
                "amount": {"value": -5.50, "currency": "EUR"},
                "status": "EXECUTED"
            },
            {
                "id": "2",
                "timestamp": "2024-05-26T10:00:00.000+0000",
                "icon": "merchant-amazon",
                "subtitle": "Marketplace",
                "title": "Amazon",
                "amount": {"value": -20.00, "currency": "EUR"},
                "status": "EXECUTED"
            },
            {
                "id": "3",
                "timestamp": "2024-05-25T10:00:00.000+0000",
                "icon": "merchant-amazon", # Refunds keep the merchant icon usually
                "subtitle": "Refund",
                "title": "Amazon",
                "amount": {"value": 20.00, "currency": "EUR"},
                "status": "EXECUTED"
            },
            { # Investment
                "id": "4",
                "timestamp": "2024-05-24T10:00:00.000+0000",
                "icon": "logos/AAPL/v2",
                "subtitle": "Buy Order",
                "title": "Apple Stock",
                "amount": {"value": -150.00, "currency": "EUR"},
                "status": "EXECUTED"
            },
            { # Failed transaction
                "id": "5",
                "timestamp": "2024-05-24T12:00:00.000+0000",
                "icon": "merchant-suspicious",
                "subtitle": "Fail",
                "title": "Suspicious Shop",
                "amount": {"value": -1000.00, "currency": "EUR"},
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
        # item 4 is investment, should be gone.
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
        self.assertEqual(t1['category'], "card")
        
        t3 = next(t for t in filtered if t['id'] == "3")
        self.assertEqual(t3['normalized_amount'], 20.00)

    def test_portfolio_analysis(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        txns = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        # In CLI, we typically use filter_all_classified() to process categories
        # Then pass that to PortfolioAnalyzer
        self.tm.transactions = txns
        all_txns_processed = self.tm.filter_all_classified()
        
        analyzer = PortfolioAnalyzer(all_txns_processed)
        report = analyzer.generate_report()
        
        print("\n--- Test Report Output ---\n" + report + "\n--------------------------")
        
        # Check Card Spending Section
        # Gross Spent: 25.50 (5.5 + 20)
        # Refunds: 20.00
        # Net Spent: 5.50 (Amazon cancels out)
        
        self.assertIn("Gross Spent:        25.50", report)
        self.assertIn("Refunds:            20.00", report)
        self.assertIn("Net Spent:           5.50", report)
        
        # Check merchants
        # Starbucks should be in top list
        self.assertIn("Starbucks", report)
        self.assertIn("5.50", report) 
        
        # Amazon should not be in "Top 10 Merchants (net)" because net > 0 check?
        # In analysis.py: [(m, a) for m, a in merchants.items() if a > 0]
        # Amazon net is 0. So it should disappear.
        self.assertNotIn("Amazon", report.split("Top 10 Merchants")[1])

    def test_csv_export(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.tm.transactions = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        filename = "test_output.csv"
        # Test normal export (not filtered by category)
        self.tm.export_to_csv(filename)
        
        self.assertTrue(os.path.exists(filename))
        
        with open(filename, 'r') as f:
            content = f.read()
            # Check headers
            self.assertIn("merchant,normalized_amount,currency,status", content)
            # Check rows
            self.assertIn("Starbucks,-5.5", content)
            self.assertIn("card", content)
            self.assertIn("investment", content)
            
        os.remove(filename)

if __name__ == '__main__':
    unittest.main()
