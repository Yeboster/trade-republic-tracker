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
                "status": "EXECUTED",
                "eventType": "card_successful_transaction"
            },
            {
                "id": "2",
                "timestamp": "2024-05-26T10:00:00.000+0000",
                "icon": "merchant-amazon",
                "subtitle": "Marketplace",
                "title": "Amazon",
                "amount": {"value": -20.00, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "card_successful_transaction"
            },
            {
                "id": "3",
                "timestamp": "2024-05-25T10:00:00.000+0000",
                "icon": "merchant-amazon", # Refunds keep the merchant icon usually
                "subtitle": "Refund",
                "title": "Amazon",
                "amount": {"value": 20.00, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "card_refund"
            },
            { # Investment
                "id": "4",
                "timestamp": "2024-05-24T10:00:00.000+0000",
                "icon": "logos/AAPL/v2",
                "subtitle": "Buy Order",
                "title": "Apple Stock",
                "amount": {"value": -150.00, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "ORDER_EXECUTED"
            },
            { # Deposit
                "id": "5",
                "timestamp": "2024-05-23T10:00:00.000+0000",
                "icon": "system",
                "subtitle": "Bank Transfer",
                "title": "Deposit",
                "amount": {"value": 1000.00, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "PAYMENT_INBOUND"
            },
            { # Withdrawal
                "id": "6",
                "timestamp": "2024-05-22T10:00:00.000+0000",
                "icon": "system",
                "subtitle": "To Checking",
                "title": "Withdrawal",
                "amount": {"value": -500.00, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "PAYMENT_OUTBOUND"
            },
            # Recurring Subscription (Netflix)
            {
                "id": "7",
                "timestamp": "2024-04-01T10:00:00.000+0000",
                "icon": "merchant-netflix",
                "subtitle": "Subscription",
                "title": "Netflix",
                "amount": {"value": -15.99, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "card_successful_transaction"
            },
            {
                "id": "8",
                "timestamp": "2024-05-01T10:00:00.000+0000",
                "icon": "merchant-netflix",
                "subtitle": "Subscription",
                "title": "Netflix",
                "amount": {"value": -15.99, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "card_successful_transaction"
            },
            {
                "id": "9",
                "timestamp": "2024-06-01T10:00:00.000+0000",
                "icon": "merchant-netflix",
                "subtitle": "Subscription",
                "title": "Netflix",
                "amount": {"value": -15.99, "currency": "EUR"},
                "status": "EXECUTED",
                "eventType": "card_successful_transaction"
            }
        ]

class TestTrackerLogic(unittest.TestCase):
    def setUp(self):
        self.mock_client = MockClient()
        self.tm = TimelineManager(self.mock_client)

    def test_classification(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.tm.transactions = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        # Test individual classifications
        t_card = next(t for t in self.tm.transactions if t['id'] == "1")
        self.assertEqual(TimelineManager.classify(t_card), "card")
        
        t_refund = next(t for t in self.tm.transactions if t['id'] == "3")
        self.assertEqual(TimelineManager.classify(t_refund), "card")
        
        t_invest = next(t for t in self.tm.transactions if t['id'] == "4")
        self.assertEqual(TimelineManager.classify(t_invest), "investment")
        
        t_deposit = next(t for t in self.tm.transactions if t['id'] == "5")
        self.assertEqual(TimelineManager.classify(t_deposit), "transfer_in")
        
        t_withdraw = next(t for t in self.tm.transactions if t['id'] == "6")
        self.assertEqual(TimelineManager.classify(t_withdraw), "transfer_out")

    def test_portfolio_analysis(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        txns = loop.run_until_complete(self.mock_client.fetch_timeline_transactions())
        
        self.tm.transactions = txns
        all_txns_processed = self.tm.filter_all_classified()
        
        analyzer = PortfolioAnalyzer(all_txns_processed)
        report = analyzer.generate_report()
        
        print("\n--- Test Report Output ---\n" + report + "\n--------------------------")
        
        # Check Overview Section
        # Card Spent: 5.50 + (15.99 * 3) = 53.47
        # Refunds: 20.00 (from Amazon) - Note: Amazon spent 20, refunded 20. Net Amazon = 0.
        # Starbucks: 5.50
        # Netflix: 47.97
        # Total Net Spent: 53.47
        self.assertIn("Net Spent", report)
        self.assertIn("53.47", report)
        
        # Check Cash Flow Section
        # Deposits: 1000.00
        # Withdrawals: 500.00
        # Net Cash Added: 500.00
        self.assertIn("Deposits:", report)
        self.assertIn("1,000.00", report)
        self.assertIn("Withdrawals:", report)
        self.assertIn("500.00", report)
        self.assertIn("Net Cash Added:", report)
        
        # Check Subscriptions
        # Netflix: 3 txns, 15.99 avg
        self.assertIn("POTENTIAL SUBSCRIPTIONS", report)
        self.assertIn("Netflix", report)
        self.assertIn("15.99", report)
        self.assertIn("Monthly", report)
        self.assertIn("Est. Monthly Cost: 15.99", report)
        
        # Check Investment Section
        # Buys: 150.00
        # Net Invested: 150.00 (since no sells)
        self.assertIn("Net Invested:", report)
        self.assertIn("150.00", report)

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
            self.assertIn("transfer_in", content)
            
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    unittest.main()
