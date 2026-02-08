import json
import time
from api.websocket_client import WebSocketClient

class TimelineClient:
    def __init__(self, token):
        self.ws_client = WebSocketClient(token)
        self.transactions = []
        self.cursor = None

    def connect(self):
        self.ws_client.connect()

    def get_transactions(self, limit=100):
        """
        Fetches transactions.
        """
        # Subscribe to timelineTransactions
        self.ws_client.subscribe(
            "timelineTransactions",
            {"after": self.cursor},
            self._on_transactions_received
        )
        
        # Wait for data (this is synchronous for now, but ideally async)
        # In a real app, this would be event-driven.
        # Here we just wait a bit for demonstration.
        time.sleep(2)
        return self.transactions

    def _on_transactions_received(self, payload):
        data = json.loads(payload)
        items = data.get("items", [])
        self.transactions.extend(items)
        
        # Check for cursor
        cursors = data.get("cursors", {})
        self.cursor = cursors.get("after")
        
        if self.cursor:
            print(f"Fetching more transactions... Cursor: {self.cursor}")
            self.ws_client.subscribe(
                "timelineTransactions",
                {"after": self.cursor},
                self._on_transactions_received
            )
        else:
            print("All transactions fetched.")
